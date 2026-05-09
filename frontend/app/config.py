"""Load settings from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class Settings:
    bucket: str
    region: str
    # Key prefix under the bucket where plugin folders live (e.g. snps/ → snps/kubernetes/...).
    snapshot_root: str
    endpoint_url: str | None
    use_ssl: bool
    addressing_style: Literal["auto", "virtual", "path"]
    list_cache_ttl_seconds: float
    snapshot_glob_prefix: str
    csv_page_size: int
    csv_max_offset: int


def _strip_slash(s: str) -> str:
    return s.strip("/")


def load_settings() -> Settings:
    bucket = os.environ.get("S3_BUCKET", "").strip()
    if not bucket:
        raise RuntimeError("S3_BUCKET is required")

    # Inner path under the bucket before `{plugin}/{snapshot}/...` (e.g. `snps`).
    # S3_SNAPSHOT_ROOT is preferred; S3_PREFIX is a backward-compatible alias.
    raw_root = os.environ.get("S3_SNAPSHOT_ROOT", "").strip()
    if not raw_root:
        raw_root = os.environ.get("S3_PREFIX", "").strip()
    snapshot_root = _strip_slash(raw_root)
    if snapshot_root:
        snapshot_root = snapshot_root + "/"

    endpoint = os.environ.get("S3_ENDPOINT_URL", "").strip() or None

    use_ssl_raw = os.environ.get("AWS_USE_SSL", "true").strip().lower()
    use_ssl = use_ssl_raw not in ("0", "false", "no")

    style = os.environ.get("S3_ADDRESSING_STYLE", "auto").strip().lower()
    if style not in ("auto", "virtual", "path"):
        style = "auto"

    ttl = float(os.environ.get("S3_LIST_CACHE_TTL_SECONDS", "45"))

    snap_prefix = os.environ.get("SNAPSHOT_FOLDER_PREFIX", "kdiff-snp-").strip() or "kdiff-snp-"

    page_size = int(os.environ.get("CSV_PAGE_SIZE", "100"))
    max_offset = int(os.environ.get("CSV_MAX_ROW_OFFSET", "500000"))

    return Settings(
        bucket=bucket,
        region=os.environ.get("S3_REGION", "us-east-1").strip() or "us-east-1",
        snapshot_root=snapshot_root,
        endpoint_url=endpoint,
        use_ssl=use_ssl,
        addressing_style=style,  # type: ignore[arg-type]
        list_cache_ttl_seconds=ttl,
        snapshot_glob_prefix=snap_prefix,
        csv_page_size=max(1, min(page_size, 5000)),
        csv_max_offset=max(0, max_offset),
    )
