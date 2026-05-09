# kdiff snapshot browser

HTMX + FastAPI UI for browsing Steampipe CSV snapshots stored in S3-compatible object storage.

## Run

From this directory:

```bash
pip install -r requirements.txt
export S3_BUCKET=your-bucket
export S3_REGION=us-east-1
# Optional for MinIO, R2, etc.:
# export S3_ENDPOINT_URL=https://minio.example.com
# export S3_ADDRESSING_STYLE=path
# export AWS_USE_SSL=true

uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open `http://localhost:8000`. Use the sidebar to pick a plugin, then a snapshot folder, then a CSV. Pagination uses row offsets on the server (streaming read).

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `S3_BUCKET` | yes | Bucket name |
| `S3_REGION` | no | Region (default `us-east-1`) |
| `S3_PREFIX` | no | Key prefix before `plugin/snapshot/...` (no leading slash; trailing slash optional) |
| `S3_ENDPOINT_URL` | no | Custom endpoint for S3-compatible APIs |
| `S3_ADDRESSING_STYLE` | no | `auto` (default), `path`, or `virtual` |
| `AWS_USE_SSL` | no | `true` / `false` for HTTP endpoints |
| `S3_LIST_CACHE_TTL_SECONDS` | no | TTL for in-memory list caches (default `45`) |
| `SNAPSHOT_FOLDER_PREFIX` | no | Only list folders under a plugin whose name starts with this (default `kdiff-snp-`) |
| `CSV_PAGE_SIZE` | no | Rows per page, max 5000 (default `100`) |
| `CSV_MAX_ROW_OFFSET` | no | Upper bound on row offset to limit deep skips (default `500000`) |

Credentials: standard AWS SDK environment variables or instance metadata (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, etc.).

## Layout

Keys are expected as:

`{S3_PREFIX}{plugin}/{kdiff-snp-YYYY-MM-DD--HH-MM}/{file}.csv`

Plugin segments must match `^[a-z0-9._-]+$`. Snapshot folders must match `kdiff-snp-YYYY-MM-DD--HH-MM`.

## Routes

- `GET /` — shell (sidebar + main)
- `GET /partials/snapshots?plugin=` — snapshot list (HTMX)
- `GET /partials/files?plugin=&snapshot=` — CSV list (HTMX)
- `GET /partials/csv?plugin=&snapshot=&file=&offset=` — table preview (HTMX)
- `GET /raw/{plugin}/{snapshot}/{filename}` — full file download
