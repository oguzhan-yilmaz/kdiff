"""S3 listing and CSV access with light caching and path validation."""

from __future__ import annotations

import csv
import io
import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, TypeVar

import boto3
from botocore.client import BaseClient
from botocore.config import Config
from botocore.exceptions import ClientError

from app.config import Settings

T = TypeVar("T")

PLUGIN_RE = re.compile(r"^[a-z0-9._-]+$")
SNAPSHOT_RE = re.compile(r"^kdiff-snp-\d{4}-\d{2}-\d{2}--\d{2}-\d{2}$")
CSV_BASENAME_RE = re.compile(r"^[a-zA-Z0-9._-]+\.csv$")


class ValidationError(ValueError):
    pass


def _cache_get(
    store: dict[str, tuple[float, Any]],
    key: str,
    ttl: float,
    factory: Callable[[], T],
) -> T:
    now = time.monotonic()
    if key in store:
        expires_at, value = store[key]
        if now < expires_at:
            return value  # type: ignore[return-value]
    value = factory()
    store[key] = (now + ttl, value)
    return value


def validate_plugin(name: str) -> str:
    if not name or not PLUGIN_RE.match(name):
        raise ValidationError("invalid plugin name")
    return name


def validate_snapshot(name: str) -> str:
    if not name or not SNAPSHOT_RE.match(name):
        raise ValidationError("invalid snapshot folder name")
    return name


def validate_csv_basename(name: str) -> str:
    if not name or "/" in name or "\\" in name:
        raise ValidationError("invalid file name")
    if not CSV_BASENAME_RE.match(name):
        raise ValidationError("invalid CSV file name")
    return name


def make_s3_client(settings: Settings) -> BaseClient:
    cfg = Config(
        signature_version="s3v4",
        s3={"addressing_style": settings.addressing_style},
    )
    return boto3.client(
        "s3",
        region_name=settings.region,
        endpoint_url=settings.endpoint_url,
        use_ssl=settings.use_ssl,
        config=cfg,
    )


def object_key(settings: Settings, plugin: str, snapshot: str, filename: str) -> str:
    p = validate_plugin(plugin)
    s = validate_snapshot(snapshot)
    f = validate_csv_basename(filename)
    return f"{settings.snapshot_root}{p}/{s}/{f}"


@dataclass(frozen=True)
class SnapshotInfo:
    name: str
    sort_key: datetime | None


def _parse_snapshot_dt(name: str) -> datetime | None:
    m = re.match(r"^kdiff-snp-(\d{4})-(\d{2})-(\d{2})--(\d{2})-(\d{2})$", name)
    if not m:
        return None
    y, mo, d, h, mi = map(int, m.groups())
    try:
        return datetime(y, mo, d, h, mi)
    except ValueError:
        return None


def _common_prefix_tail(prefix: str, base: str) -> str | None:
    if not prefix.startswith(base):
        return None
    rest = prefix[len(base) :].strip("/")
    if not rest:
        return None
    return rest.split("/", 1)[0]


class S3Browser:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = make_s3_client(settings)
        self._list_cache: dict[str, tuple[float, Any]] = {}

    def _ttl(self) -> float:
        return self._settings.list_cache_ttl_seconds

    def list_plugins(self) -> list[str]:
        base = self._settings.snapshot_root

        def load() -> list[str]:
            names: list[str] = []
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(
                Bucket=self._settings.bucket,
                Prefix=base,
                Delimiter="/",
            ):
                for cp in page.get("CommonPrefixes") or []:
                    p = cp.get("Prefix") or ""
                    tail = _common_prefix_tail(p, base)
                    if tail and PLUGIN_RE.match(tail):
                        names.append(tail)
            names.sort(key=str.lower)
            return names

        return _cache_get(self._list_cache, f"plugins:{base}", self._ttl(), load)

    def list_snapshots(self, plugin: str) -> list[SnapshotInfo]:
        p = validate_plugin(plugin)
        base = f"{self._settings.snapshot_root}{p}/"

        def load() -> list[SnapshotInfo]:
            infos: list[SnapshotInfo] = []
            latest: dict[str, datetime] = {}
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(
                Bucket=self._settings.bucket,
                Prefix=base,
                Delimiter="/",
            ):
                for cp in page.get("CommonPrefixes") or []:
                    prefix = cp.get("Prefix") or ""
                    name = _common_prefix_tail(prefix, base)
                    if not name:
                        continue
                    if not name.startswith(self._settings.snapshot_glob_prefix):
                        continue
                    if not SNAPSHOT_RE.match(name):
                        continue
                    sk = _parse_snapshot_dt(name)
                    infos.append(SnapshotInfo(name=name, sort_key=sk))
                for obj in page.get("Contents") or []:
                    key = obj.get("Key") or ""
                    if not key.startswith(base):
                        continue
                    rel = key[len(base) :]
                    seg = rel.split("/", 1)[0]
                    if not seg.startswith(self._settings.snapshot_glob_prefix):
                        continue
                    if not SNAPSHOT_RE.match(seg):
                        continue
                    lm = obj.get("LastModified")
                    if isinstance(lm, datetime):
                        prev = latest.get(seg)
                        if prev is None or lm > prev:
                            latest[seg] = lm

            merged: dict[str, SnapshotInfo] = {}
            for info in infos:
                merged[info.name] = info
            for seg, lm in latest.items():
                if seg not in merged:
                    merged[seg] = SnapshotInfo(name=seg, sort_key=lm)

            out = list(merged.values())

            def sort_tuple(i: SnapshotInfo) -> tuple:
                if i.sort_key is not None:
                    return (0, i.sort_key)
                return (1, datetime.min)

            out.sort(key=sort_tuple, reverse=True)
            return out

        return _cache_get(self._list_cache, f"snapshots:{base}", self._ttl(), load)

    def list_csv_files(self, plugin: str, snapshot: str) -> list[str]:
        p = validate_plugin(plugin)
        s = validate_snapshot(snapshot)
        prefix = f"{self._settings.snapshot_root}{p}/{s}/"

        def load() -> list[str]:
            names: list[str] = []
            paginator = self._client.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=self._settings.bucket, Prefix=prefix):
                for obj in page.get("Contents") or []:
                    key = obj.get("Key") or ""
                    if not key.startswith(prefix) or key.endswith("/"):
                        continue
                    base = key.rsplit("/", 1)[-1]
                    if CSV_BASENAME_RE.match(base):
                        names.append(base)
            names.sort(key=str.lower)
            return names

        return _cache_get(self._list_cache, f"files:{prefix}", self._ttl(), load)

    def read_csv_page(
        self,
        plugin: str,
        snapshot: str,
        filename: str,
        *,
        data_row_offset: int,
        page_size: int,
    ) -> tuple[list[str], list[list[str]], bool]:
        key = object_key(self._settings, plugin, snapshot, filename)
        try:
            resp = self._client.get_object(Bucket=self._settings.bucket, Key=key)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            raise FileNotFoundError(code or "GetObject failed") from e

        body = resp["Body"]
        text = io.TextIOWrapper(body, encoding="utf-8", newline="")
        reader = csv.reader(text)
        try:
            header = next(reader)
        except StopIteration:
            return [], [], False

        skipped = 0
        rows: list[list[str]] = []
        for row in reader:
            if skipped < data_row_offset:
                skipped += 1
                continue
            rows.append(row)
            if len(rows) >= page_size:
                break

        has_more = False
        for _ in reader:
            has_more = True
            break

        return header, rows, has_more

    def open_raw_stream(self, plugin: str, snapshot: str, filename: str) -> tuple[Any, str | None]:
        key = object_key(self._settings, plugin, snapshot, filename)
        try:
            resp = self._client.get_object(Bucket=self._settings.bucket, Key=key)
        except ClientError as e:
            code = e.response.get("Error", {}).get("Code", "")
            raise FileNotFoundError(code or "GetObject failed") from e
        body = resp["Body"]
        etag = resp.get("ETag")
        if isinstance(etag, str):
            etag = etag.strip('"')
        return body, etag
