from datetime import datetime
import streamlit as st
from config import boto3_session
from storage import *
from pathlib import Path
import json
import pandas as pd
from st_aggrid import AgGrid, GridOptionsBuilder


# Main page content
st.markdown("# List of snapshots on remote S3")
st.sidebar.markdown("## List of snapshots on remote S3")
# print(dir(bucket))
# print('-'*20)
# print(dir(bucket.Tagging))
# print(bucket.bucket_arn, bucket.bucket_region, bucket.creation_date)
# print(bucket.get_available_subresources())

def main():
    s3_snapshot_dirs = get_kdiff_snapshot_metadata_files('test-bucket')

    snapshot_list = []

    for mf in s3_snapshot_dirs:
        data =mf['file_content']

        snapshot_info = data.get("snapshotInfo", {})
        cli_versions = data.get("cliVersions", {})
        checksums = data.get("checksums", {})

        # Parse timestamp string into datetime object
        timestamp = snapshot_info.get("timestamp")
        timestamp_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        snapshot_list.append({
            "Timestamp": timestamp_dt,
            # "Hostname": snapshot_info.get("hostname"),
            "Output Directory": snapshot_info.get("output_directory"),
            "S3 Bucket": snapshot_info.get("s3_bucket_name"),
            "File Count": len(checksums),
            # "kubectl Version": cli_versions.get("kubectl"),
            # "AWS CLI Version": cli_versions.get("aws"),
            # "Steampipe Version": cli_versions.get("steampipe")
        })

    df_snapshots = pd.DataFrame(snapshot_list)

    # --- Date range filter ---
    min_date = df_snapshots['Timestamp'].min().date()
    max_date = df_snapshots['Timestamp'].max().date()
    selected_range = st.sidebar.date_input(
        "Filter snapshots by date",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )

    # Filter DataFrame by selected date range
    if isinstance(selected_range, tuple) and len(selected_range) == 2:
        start_date, end_date = selected_range
        df_snapshots = df_snapshots[
            (df_snapshots['Timestamp'].dt.date >= start_date) &
            (df_snapshots['Timestamp'].dt.date <= end_date)
        ]

    # --- Interactive table ---
    gb = GridOptionsBuilder.from_dataframe(df_snapshots)
    gb.configure_default_column(sortable=True, filter=True)
    gb.configure_selection(selection_mode="single", use_checkbox=True)
    grid_options = gb.build()

    AgGrid(df_snapshots, gridOptions=grid_options, height=400, fit_columns_on_grid_load=True)

if __name__ == '__main__':
    main()