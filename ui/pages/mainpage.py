"""
KDiff Backup Dashboard — Main page showing S3 backup status per plugin.
Each plugin gets its own dashboard section with backup counts, timeseries, and health metrics.
"""
from datetime import datetime, timedelta, timezone

import altair as alt
import pandas as pd
import streamlit as st

from config import bucket_name, snapshots_s3_prefix, ui_config
from storage import get_kdiff_snapshot_metadata_files_for_plugin, list_folders

st.set_page_config(layout="wide", page_title="KDiff Backup Dashboard")

def _check_s3_connection():
    """Verify S3 bucket is reachable."""
    try:
        from config import boto3_session
        client = boto3_session.client("s3")
        client.head_bucket(Bucket=bucket_name)
        return True, None
    except Exception as e:
        return False, str(e)


@st.cache_data(ttl=60)
def _load_plugin_backups():
    """Load backup metadata for all plugins. Cached 60s."""
    plugins = list_folders(bucket_name, snapshots_s3_prefix)
    result = {}
    for plugin in plugins:
        try:
            snapshots = get_kdiff_snapshot_metadata_files_for_plugin(bucket_name, plugin)
            result[plugin] = snapshots
        except Exception as e:
            result[plugin] = {"_error": str(e)}
    return result


def _plugin_cron(plugin_name: str) -> str | None:
    """Get cron_schedule for plugin from config if set."""
    plugins = ui_config.get("plugins", {})
    conf = plugins.get(plugin_name, {})
    return conf.get("cron_schedule")


def _build_timeseries_df(snapshots: list, freq: str) -> pd.DataFrame:
    """Build aggregated backup counts by period (D=day, W=week, M=month)."""
    if not snapshots or isinstance(snapshots, dict):
        return pd.DataFrame()
    df = pd.DataFrame([{"ts": s["timestampObj"]} for s in snapshots])
    df["period"] = df["ts"].dt.to_period(freq).astype(str)
    return df.groupby("period", as_index=False).size().rename(columns={"size": "backups"})


def _render_plugin_dashboard(plugin_name: str, snapshots: list):
    """Render a single plugin's dashboard section."""
    if isinstance(snapshots, dict) and "_error" in snapshots:
        st.error(f"Failed to load {plugin_name}: {snapshots['_error']}")
        return

    cron = _plugin_cron(plugin_name)
    n = len(snapshots)

    # Header row: plugin name + cron + metrics
    cols = st.columns([2, 1, 1, 1, 1])
    with cols[0]:
        st.subheader(f"📦 {plugin_name}")
    with cols[1]:
        if cron:
            st.caption("Cron")
            st.code(cron, language=None)
        else:
            st.caption("Cron")
            st.caption("—")
    with cols[2]:
        st.metric("Total backups", n)
    with cols[3]:
        if snapshots:
            latest = max(s["timestampObj"] for s in snapshots)
            st.metric("Latest", latest.strftime("%Y-%m-%d %H:%M"))
        else:
            st.metric("Latest", "—")
    with cols[4]:
        if snapshots:
            oldest = min(s["timestampObj"] for s in snapshots)
            st.metric("Oldest", oldest.strftime("%Y-%m-%d"))
        else:
            st.metric("Oldest", "—")

    if not snapshots:
        st.info(f"No backups found for **{plugin_name}** in S3.")
        return

    # Timeseries charts
    freq_map = {"Daily": "D", "Weekly": "W", "Monthly": "M"}
    selected_freq = st.radio(
        "Aggregation",
        options=list(freq_map.keys()),
        horizontal=True,
        key=f"freq_{plugin_name}",
    )
    freq = freq_map[selected_freq]
    ts_df = _build_timeseries_df(snapshots, freq)
    if ts_df.empty:
        st.caption("No timeseries data.")
        return

    chart = (
        alt.Chart(ts_df)
        .mark_bar()
        .encode(
            x=alt.X("period:N", sort=None, title=selected_freq),
            y=alt.Y("backups:Q", title="Backups"),
            color=alt.value("#1f77b4"),
        )
        .properties(height=220, title=f"Backups per {selected_freq}")
    )
    st.altair_chart(chart, use_container_width=True)

    # Extra: last 7 days activity, avg backups per period
    df_all = pd.DataFrame([{"ts": s["timestampObj"]} for s in snapshots])
    df_all["date"] = df_all["ts"].dt.date
    cutoff = datetime.now(timezone.utc) - timedelta(days=7)
    recent = df_all[df_all["ts"] >= cutoff]
    avg_per_period = ts_df["backups"].mean()

    ex1, ex2, ex3 = st.columns(3)
    with ex1:
        st.caption("Last 7 days")
        st.metric("Backups", len(recent))
    with ex2:
        st.caption(f"Avg per {selected_freq}")
        st.metric("Backups", f"{avg_per_period:.1f}")
    with ex3:
        if len(snapshots) >= 2:
            timestamps = sorted(s["timestampObj"] for s in snapshots)
            gaps = [(timestamps[i + 1] - timestamps[i]).total_seconds() / 3600 for i in range(len(timestamps) - 1)]
            avg_gap_h = sum(gaps) / len(gaps)
            st.caption("Avg gap between backups")
            st.metric("Hours", f"{avg_gap_h:.1f}")
        else:
            st.caption("Avg gap")
            st.metric("Hours", "—")


# ----- Page content -----
st.markdown("# KDiff Backup Dashboard")
st.caption("S3 backup status for each Steampipe plugin. Each plugin can have its own cron schedule.")

# S3 connection check
ok, err = _check_s3_connection()
if not ok:
    st.error(f"Cannot connect to S3 bucket `{bucket_name}`: {err}")
    st.stop()

st.success(f"Connected to S3 bucket `{bucket_name}`")

# Load data
with st.spinner("Loading backup metadata from S3…"):
    all_backups = _load_plugin_backups()

if not all_backups:
    st.warning("No plugins found in S3. Check your bucket prefix and backup jobs.")
    st.stop()

# Summary at top
total_backups = sum(
    len(v) for v in all_backups.values()
    if isinstance(v, list)
)
s1, s2, s3 = st.columns(3)
with s1:
    st.metric("Total plugins", len(all_backups))
with s2:
    st.metric("Total backups (all plugins)", total_backups)
with s3:
    st.metric("S3 prefix", snapshots_s3_prefix or "—")

st.divider()

# Per-plugin dashboards
for plugin_name in sorted(all_backups.keys()):
    snapshots = all_backups[plugin_name]
    with st.expander(f"**{plugin_name}** — {len(snapshots) if isinstance(snapshots, list) else 0} backups", expanded=True):
        _render_plugin_dashboard(plugin_name, snapshots)
    st.divider()
