
Here is a **prompt-ready summary** of the current `ui/` app you can hand to another tool or session.

---

## KDiff UI — summary for rewrite (Streamlit → JS or other)

### Purpose
Internal **backup / snapshot browser** for KDiff: list what lives in S3 under a configurable prefix, then **open a snapshot** and explore its **CSV tables** with filters driven by snapshot metadata and a **YAML plugin config**.

### Stack today
- **Python 3.13**, **Streamlit** (multi-page app via `st.navigation`).
- **boto3** for S3 (list prefixes, list/download `kdiff-snapshot.metadata.json`).
- **pandas** for CSV read and in-memory filtering.
- **python-dotenv** + **PyYAML** for env and `plugin-config.yaml`.
- **AWS CLI** (`aws s3 sync`) invoked from Python to mirror snapshot folders to a local directory (`KDIFF_SNAPSHOTS_DIR`).
- **Docker**: slim Python image, `uv sync`, `streamlit run streamlit_app.py` on port 8501.

`pyproject.toml` also lists **streamlit-aggrid**, **streamlit-calendar**, **pygwalker**, etc.; **they are not imported** in the current `.py` sources—active UI is Streamlit widgets + `st.dataframe`.

### Entry and routing
- **`streamlit_app.py`**: navigation with two pages only:
  - **Home** → `pages/mainpage.py`
  - **multi-context** → `pages/multi-context.py`, URL path `multi-context`
- Several other pages are commented out (diff / alternate flows).

### Configuration
- **Env**: `BUCKET_NAME` (required), `S3_UPLOAD_PREFIX` (snapshots root in bucket), optional AWS keys/region, `KDIFF_SNAPSHOTS_DIR` (local sync target), `KDIFF_LOCAL_DIFF_DIR` (declared in config; usage varies).
- **`plugin-config.yaml`**: per-plugin rules:
  - `divide_columns`: column names used to build extra **multiselect filters** (e.g. Kubernetes `namespace`).
  - `_default.hide_columns`, per-`tables.<name>.unique_columns`, `show_first`, `hide_columns`.
  - Optional `diffs.unique_column` (for diff tooling; see below).

### Data model (S3 layout)
- Under `s3://{BUCKET}/{S3_UPLOAD_PREFIX}/`, **first-level “folders” = plugin names**.
- Each snapshot is a directory containing **`kdiff-snapshot.metadata.json`** (plus CSVs referenced by checksums).
- Metadata is JSON with at least: `snapshotInfo.timestamp`, `checksums` (map filename → …), and optionally **`dividers.sp_connection_name`** (list of SP connection labels for filtering).

### Home page (`mainpage.py`)
- Wide layout, title **KDiff Backup Dashboard**.
- Lists plugins from S3; for each plugin loads all metadata files and shows:
  - **Metrics**: backup count and “days since latest” (from snapshot timestamp vs now UTC).
  - **Table per plugin**: each row links to **`multi-context?plugin=…&snapshot=…`** (URL-encoded plugin; snapshot name in query for deep link).

### Multi-context page (`multi-context.py`)
- **Sidebar**
  - Plugin **radio** (options = S3 plugin folders); default from `?plugin=`.
  - **Date** then **time** selectboxes derived from metadata timestamps; default from `?snapshot=` when plugin matches query.
- **URL state**: writes `plugin` and `snapshot` query params when selections change (shareable links).
- **Main area**
  - **SP Connection** sidebar pills when `dividers.sp_connection_name` exists (multi-select; default all). Filters rows where column `sp_connection_name` is in selection (skip filter if all selected).
  - **Objects** multiselect: keys of `checksums` in selected snapshot (display strips `{plugin}_` prefix and `.csv`).
  - **Sliders**: row height and table height for `st.dataframe`.
- **Load path**
  1. `sync_kdiff_snapshot_to_local_filesystem`: `aws s3 sync` from `s3://bucket/{snapshot_dir}` into `{KDIFF_SNAPSHOTS_DIR}/{snapshot_dir}`.
  2. Read selected CSVs with pandas.
  3. Apply **`plugin-config.yaml`**: drop default/hidden columns, reorder with `show_first`.
  4. Build **divider** multiselects from unique values of `divide_columns` across loaded frames; filter rows by those columns.
  5. One **section per table** (`st.dataframe`), skip empty after filters.

### Supporting modules
- **`storage.py`**: S3 client, list folder prefixes, find/download metadata per plugin, merge parsed JSON into snapshot records (`timestampObj`, `snapshot_dir`, `snapshot_name`, `s3_last_modified`, etc.).
- **`s3_and_local_files.py`**: `aws s3 sync` wrapper; `run_any_bash_command` for shell pipelines.
- **`diff_csv.py`**: **`qsv diff`**-based comparison of two CSVs keyed by a column, optionally scoped by `sp_connection_name`—**not wired** in the two active Streamlit pages (legacy / future).
- **`misc.py`**: not opened; treat as small helpers if present.

### UX / product notes for a rewrite
- Treat **Home** as an **S3 health / inventory** view and **multi-context** as **snapshot explorer** with deep linking.
- Preserve **query params** `plugin` and `snapshot` for bookmarks and links from the dashboard.
- **Server-side** today: boto3 + optional sync need a **backend** (or edge functions) in a JS app unless you move to pre-signed URLs / direct S3 from browser with IAM constraints.
- **Note**: the copy of `multi-context.py` in your tree may currently contain **typos** in imports (`fimport`, `storagef`); `mainpage.py` uses the correct `storage` import—fix or ignore when describing “intended” behavior.

### README discrepancy
- `README.md` suggests `uv run streamlit run mainpage.py`; **Docker and full nav** use **`streamlit_app.py`**.

---

You can paste the block above as the **“spec”** for “reimplement this UI in React/Next/Svelte/etc. with a small API for S3/metadata/sync.” If you want, we can tighten it for a specific target (e.g. “Next.js + S3 presigned” only) in a follow-up.