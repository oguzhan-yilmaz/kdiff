
import streamlit as st
st.set_page_config(layout="wide")

from typing import List, DefaultDict, Dict
from datetime import datetime
from config import boto3_session, bucket_name
from storage import *
from pathlib import Path
import json
import pandas as pd

# --------- + init params ---------
selected_snapshot = None
sidebar_plugin_param = None
selected_date = None
selected_time = None
# --------- / init params ---------

s3_remote_available_plugins = list_folders(bucket_name, 'snps')
sidebar_plugin_param = st.sidebar.radio(
        "Plugin Name",s3_remote_available_plugins,
        index=0,
        format_func=lambda a: f"**{a}**"
    )



popover = st.popover("Filter items")
red = popover.checkbox("Show red items.", True)
blue = popover.checkbox("Show blue items.", True)

if red:
    st.write(":red[This is a red item.]")
if blue:
    st.write(":blue[This is a blue item.]")



s3_snapshots = get_kdiff_snapshot_metadata_files_for_plugin(bucket_name, sidebar_plugin_param)
s3_snapshots_df = pd.DataFrame(s3_snapshots)
# s3_snapshots_df
# print(json.dumps(s3_snapshots, indent=2, default=str))
_conf = {
    "pluginname": {
        "sidebar": {
            
        }
    }
}


def set_sidebar_params():
    # ---- SIDEBAR PARAMS ----
    # st.markdown("# set_sidebar_params")
    

    # snapshot_list
    # s3_snapshots
    if not s3_snapshots:
        {"failed": "s3_snapshots empty", "s3_snapshots": s3_snapshots}
        st.sidebar.markdown(f"No snapshots are found")
        st.exception(f"No snapshots are found for {sidebar_plugin_param}")
            
    # Extract date and time columns
    s3_snapshots_df["date"] = s3_snapshots_df["timestampObj"].dt.date
    s3_snapshots_df["time"] = s3_snapshots_df["timestampObj"].dt.strftime("%H:%M:%S")

    # --- Sidebar DATE selector ---
    unique_dates = sorted(s3_snapshots_df["date"].unique())

    # unique_dates

    selected_date = st.sidebar.date_input(
        "Select a snapshot date",
        value=unique_dates[-1],            # default = latest date
        min_value=min(unique_dates),
        max_value=max(unique_dates),
    )

    # --- Filter snapshots for the selected date ---
    df_for_date = s3_snapshots_df[s3_snapshots_df["date"] == selected_date]

    # Show times belonging to that date
    time_options = df_for_date["time"].tolist()

    selected_time = st.sidebar.selectbox(
        "Select a snapshot time",
        options=time_options,
    )

    # --- Find the selected snapshot row ---
    selected_snapshot = df_for_date[df_for_date["time"] == selected_time].iloc[0]
    return selected_snapshot


selected_snapshot = set_sidebar_params()

on = st.sidebar.toggle("Activate feature")

if on:
    st.write("Feature activated!")
# s3_snapshots_df
# selected_snapshot

def csv_to_dataclass(csv_file_path: Path, dataclass_table: Dict):
    """
    Read CSV file and convert rows to dataclass instances
    """
    try:
        df = pd.read_csv(csv_file_path)
        return df
    except Exception as e:
        # st.exception(e)
        f"- not generated as it doesnt have namespace{csv_file_path}"
        return pd.DataFrame()

def show_selected_snapshot_tables(snapshot: pd.DataFrame):
    st.markdown("#### snapshot DF")
    # snapshot
    snapshot_dict = snapshot.to_dict()
    # snapshot_dict
    sync_kdiff_snapshot_to_local_filesystem(snapshot_dict)
    
    checksums = snapshot_dict['checksums']
    snp_path = Path(local_dir_for_s3_sync) / snapshot_dict['snapshot_dir']
    filenames = set(checksums.keys())
    
    selected_filenames = st.multiselect(
        "Select filenames?",
        filenames,
        default=filenames,
        # width="stretch",
        width=600,
        format_func=lambda s: s.replace(f"{sidebar_plugin_param}_", "").replace(".csv", "")
    )
    
    for filename in selected_filenames:
        _file_path = snp_path / filename
        A_df = csv_to_dataclass(_file_path, {})
        if not A_df.empty:
            st.markdown(f"###### {filename}")
            A_df

    # selected_filenames
    snapshot_path = Path(local_dir_for_s3_sync) / snapshot_dict['snapshot_dir']

    pass

show_selected_snapshot_tables(selected_snapshot)
# show tables