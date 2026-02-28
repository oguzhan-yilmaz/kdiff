"""
KDiff Backup Dashboard — Main page showing current S3 backup status per plugin.
"""
from urllib.parse import quote

import pandas as pd
import streamlit as st

st.set_page_config(layout="wide", page_title="KDiff Backup Dashboard")

try:
    from config import bucket_name, snapshots_s3_prefix
    from storage import get_kdiff_snapshot_metadata_files_for_plugin, list_folders
except ValueError as e:
    st.error("Configuration error")
    st.error(str(e))
    st.info(
        "Please set the **BUCKET_NAME** environment variable to connect to your S3 bucket. "
        "You can also set **AWS_ACCESS_KEY_ID**, **AWS_SECRET_ACCESS_KEY**, and **AWS_DEFAULT_REGION** if needed."
    )
    st.stop()

# ---- Current backup status (what's in S3) ----
st.header("Current backup status")
st.caption(f"s3://{bucket_name}/{snapshots_s3_prefix}")

try:
    s3_plugins = list_folders(bucket_name, snapshots_s3_prefix)
except Exception as e:
    st.error(f"Failed to list S3: {e}")
    st.info("Check that BUCKET_NAME and S3_UPLOAD_PREFIX are correct and you have S3 access.")
    st.stop()

if not s3_plugins:
    st.warning(f"No plugin folders found in s3://{bucket_name}/{snapshots_s3_prefix}")
    st.stop()

# Summary: which plugins have backups, counts, latest
backup_rows = []
for plugin in sorted(s3_plugins):
    snapshots = get_kdiff_snapshot_metadata_files_for_plugin(bucket_name, plugin)
    count = len(snapshots)
    latest = max(snapshots, key=lambda s: s["timestampObj"]) if snapshots else None
    backup_rows.append({
        "Plugin": plugin,
        "Backup count": count,
        "Latest backup": latest["display_date"] + " " + latest["display_time"] if latest else "—",
    })

st.dataframe(backup_rows, use_container_width=True, hide_index=True)

# Backups per plugin as data tables
st.subheader("Backups per plugin")
for plugin in sorted(s3_plugins):
    snapshots = get_kdiff_snapshot_metadata_files_for_plugin(bucket_name, plugin)
    if not snapshots:
        continue
    rows = []
    for s in sorted(snapshots, key=lambda x: x["timestampObj"], reverse=True):
        s3_uploaded = s.get("s3_last_modified")
        s3_str = s3_uploaded.strftime("%Y-%m-%d %H:%M") if s3_uploaded else "—"
        # Use unencoded snapshot in URL so regex can extract it for display
        link = f"multi-context?plugin={quote(plugin)}&snapshot={s['snapshot_name']}"
        rows.append({
            "Snapshot": link,
            "S3 uploaded": s3_str,
        })
    df = pd.DataFrame(rows)
    st.markdown(f"**{plugin}**")
    st.dataframe(
        df,
        column_config={
            "Snapshot": st.column_config.LinkColumn(
                "Snapshot",
                display_text=r"snapshot=([^&]+)",
            ),
        },
        use_container_width=True,
        hide_index=True,
    )
