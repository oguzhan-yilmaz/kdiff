
import streamlit as st
st.set_page_config(layout="wide")

from typing import List, DefaultDict, Dict
from datetime import datetime
from config import boto3_session, bucket_name, ui_config
from storage import *
from pathlib import Path
import json
import pandas as pd

# --------- + init params ---------
selected_snapshot = None
sidebar_plugin_param = None
selected_date = None
selected_time = None
row_height_slider = None
# --------- / init params ---------

s3_remote_available_plugins = list_folders(bucket_name, 'snps')
sidebar_plugin_param = st.sidebar.radio(
        "Plugin Name",s3_remote_available_plugins,
        index=0,
        format_func=lambda a: f"**{a}**"
    )



popover = st.popover(":rainbow[View Options (row height, etc..)]", icon=":material/settings:",)  #  type='primary'
row_height_slider = popover.slider("Row Height", 10, 120, 20, key="row_height")
_min_table_height = 300
table_height_slider = popover.slider("Table Height", _min_table_height, 2000, _min_table_height, key="table_height")
if table_height_slider == _min_table_height:
    table_height_slider = 'auto'
    
# _min_table_width = 300
# table_width_slider = popover.slider("Table width", _min_table_width, 2000, _min_table_width, key="table_width")
# if table_width_slider == _min_table_width:
#     table_width_slider = 'stretch'
# red = popover.checkbox("Show red items.", True)
# blue = popover.checkbox("Show blue items.", True)
# st.write("I'm ", row_height_slider, "years old")
# if red:
#     st.write(":red[This is a red item.]")
# if blue:
#     st.write(":blue[This is a blue item.]")



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
        key="selected_time"
    )

    # --- Find the selected snapshot row ---
    selected_snapshot = df_for_date[df_for_date["time"] == selected_time].iloc[0]
    return selected_snapshot


selected_snapshot = set_sidebar_params()

# on = st.sidebar.toggle("Activate feature")

# if on:
#     st.write("Feature activated!")


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
    
    r = {}
    for filename in selected_filenames:
        _file_path = snp_path / filename
        A_df = csv_to_dataclass(_file_path, {})
        if not A_df.empty:
            
            plugin_name = sidebar_plugin_param
            table_name = filename.replace(f"{plugin_name}_", "").replace(".csv", "")
            ui_config.get('plugins', {}).get(plugin_name, {}).get('tables', {})
            plugins_config = ui_config.get('plugins', {})
            _default_hide_cols = plugins_config.get('_default', {}).get('hide_columns', [])
            table_config = plugins_config.get(plugin_name, {}).get(table_name, {})
            hide_columns = table_config.get('hide_columns', [])
            hide_columns.extend(_default_hide_cols)
            # table_config
            processed_df = A_df
            if table_config:
                if hide_columns:
                    processed_df = A_df.drop(columns=hide_columns, errors='ignore')

                show_first_cols = table_config.get('show_first', [])
                
                all_cols = list(processed_df.columns)
                show_first_cols = [c for c in show_first_cols if c in all_cols]

                if show_first_cols:
                    display_cols = show_first_cols
                    remaining_cols = [c for c in all_cols if c not in show_first_cols]
                    display_cols.extend(remaining_cols)
                    processed_df = processed_df[display_cols]

            r[filename] = {
                'filepath': _file_path,
                'filename': filename,
                'dataframe': A_df,
                'tablename': table_name,
            }

    # selected_filenames
    snapshot_path = Path(local_dir_for_s3_sync) / snapshot_dict['snapshot_dir']
    return r
    pass

snapshot_dataframe_list = show_selected_snapshot_tables(selected_snapshot)
for snp_df_item in snapshot_dataframe_list.values():
    # snp_df_item
    table_name = snp_df_item['tablename']
    snp_df = snp_df_item['dataframe']
    st.markdown(f"###### {table_name}")
    st.dataframe(
        snp_df,
        row_height=row_height_slider,
        height=table_height_slider,
        # width='stretch',
        # width=table_width_slider,
    )

# snapshot_dataframes