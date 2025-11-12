from datetime import datetime
import streamlit as st
from config import boto3_session, bucket_name
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

def list_snapshots_on_s3():
    
    s3_snapshot_dirs = get_kdiff_snapshot_metadata_files(bucket_name)
    # s3_snapshot_dirs
    snapshot_list = []

    # for mf in s3_snapshot_dirs:
    for mf in s3_snapshot_dirs[:2]:
        data =mf['metadata_json']

        snapshot_info = data.get("snapshotInfo", {})
        cli_versions = data.get("cliVersions", {})
        checksums = data.get("checksums", {})
        # snapshot_info
        # checksums
        # Parse timestamp string into datetime object
        timestamp = snapshot_info.get("timestamp")
        timestamp_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))

        snapshot_list.append({
            "Timestamp": timestamp_dt,
            # "Hostname": snapshot_info.get("hostname"),
            "Output Directory": snapshot_info.get("output_directory"),
            # "S3 Bucket": snapshot_info.get("s3_bucket_name"),
            "Hostname": snapshot_info.get("hostname"),
            "File Count": len(checksums.keys()),
            # "Remote URL": 
            # "kubectl Version": cli_versions.get("kubectl"),
            # "AWS CLI Version": cli_versions.get("aws"),
            # "Steampipe Version": cli_versions.get("steampipe")
        })
    return snapshot_list


def main():
    x = list_snapshots_on_s3()
    x
    pass
if __name__ == '__main__':
    main()