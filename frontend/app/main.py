"""HTMX + FastAPI snapshot browser."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path

from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from starlette.templating import Jinja2Templates

from app.config import Settings, load_settings
from app.s3_browser import S3Browser, ValidationError

_templates_dir = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(_templates_dir))


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    app.state.settings = settings
    app.state.browser = S3Browser(settings)
    yield


app = FastAPI(title="kdiff snapshot browser", lifespan=lifespan)


def _browser(request: Request) -> S3Browser:
    return request.app.state.browser


def _settings(request: Request) -> Settings:
    return request.app.state.settings


def _is_htmx(request: Request) -> bool:
    return request.headers.get("hx-request", "").lower() == "true"


def _error_response(request: Request, message: str, status_code: int = 400) -> HTMLResponse:
    if _is_htmx(request):
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"message": message},
            status_code=200,
        )
    return HTMLResponse(f"<html><body><pre>{message}</pre></body></html>", status_code=status_code)


@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    try:
        plugins = _browser(request).list_plugins()
    except ClientError as e:
        return _error_response(request, f"S3 error: {e}", 502)
    return templates.TemplateResponse(
        request=request,
        name="base.html",
        context={"plugins": plugins, "title": "kdiff"},
    )


@app.get("/partials/sidebar-plugins", response_class=HTMLResponse)
def partial_sidebar_plugins(request: Request):
    try:
        plugins = _browser(request).list_plugins()
    except ClientError as e:
        return _error_response(request, f"S3 error: {e}", 502)
    return templates.TemplateResponse(
        request=request,
        name="partials/sidebar_plugins.html",
        context={"plugins": plugins},
    )


@app.get("/partials/snapshots", response_class=HTMLResponse)
def partial_snapshots(request: Request, plugin: str):
    try:
        snaps = _browser(request).list_snapshots(plugin)
    except ValidationError as e:
        return _error_response(request, str(e))
    except ClientError as e:
        return _error_response(request, f"S3 error: {e}", 502)
    return templates.TemplateResponse(
        request=request,
        name="partials/snapshots.html",
        context={"plugin": plugin, "snapshots": snaps},
    )


@app.get("/partials/files", response_class=HTMLResponse)
def partial_files(request: Request, plugin: str, snapshot: str):
    try:
        files = _browser(request).list_csv_files(plugin, snapshot)
    except ValidationError as e:
        return _error_response(request, str(e))
    except ClientError as e:
        return _error_response(request, f"S3 error: {e}", 502)
    return templates.TemplateResponse(
        request=request,
        name="partials/files.html",
        context={"plugin": plugin, "snapshot": snapshot, "files": files},
    )


@app.get("/partials/csv", response_class=HTMLResponse)
def partial_csv(request: Request, plugin: str, snapshot: str, file: str, offset: int = 0):
    settings = _settings(request)
    if offset < 0:
        return _error_response(request, "offset must be non-negative")
    if offset > settings.csv_max_offset:
        return _error_response(request, "offset too large")

    page_size = settings.csv_page_size
    try:
        header, rows, has_more = _browser(request).read_csv_page(
            plugin,
            snapshot,
            file,
            data_row_offset=offset,
            page_size=page_size,
        )
    except ValidationError as e:
        return _error_response(request, str(e))
    except FileNotFoundError as e:
        return _error_response(request, str(e), 404)
    except ClientError as e:
        return _error_response(request, f"S3 error: {e}", 502)

    next_offset = offset + len(rows) if has_more else None
    return templates.TemplateResponse(
        request=request,
        name="partials/csv.html",
        context={
            "plugin": plugin,
            "snapshot": snapshot,
            "file": file,
            "header": header,
            "rows": rows,
            "offset": offset,
            "page_size": page_size,
            "has_more": has_more,
            "next_offset": next_offset,
        },
    )


@app.get("/raw/{plugin}/{snapshot}/{filename}")
def raw_csv(plugin: str, snapshot: str, filename: str, request: Request):
    try:
        body, _etag = _browser(request).open_raw_stream(plugin, snapshot, filename)
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ClientError as e:
        raise HTTPException(status_code=502, detail=f"S3 error: {e}") from e

    def stream():
        try:
            while True:
                chunk = body.read(64 * 1024)
                if not chunk:
                    break
                yield chunk
        finally:
            body.close()

    return StreamingResponse(
        stream(),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )
