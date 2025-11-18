
import streamlit as st
st.set_page_config(layout="wide")

from typing import List, DefaultDict, Dict
from datetime import datetime
from config import boto3_session, bucket_name, ui_config, snapshots_s3_prefix
from storage import *
from pathlib import Path
import json
import pandas as pd

# --------- + init params ---------
selected_snapshot = None
# sidebar_plugin_param = None
selected_date = None
selected_time = None
row_height_slider = None
# --------- / init params ---------

s3_remote_available_plugins = list_folders(bucket_name, snapshots_s3_prefix)
sidebar_plugin_param = st.sidebar.radio(
        "Plugin Name",s3_remote_available_plugins,
        index=0,
        format_func=lambda a: f"**{a}**"
    )

plugin_name = sidebar_plugin_param
plugins_config = ui_config.get('plugins', {})
current_plugin_conf = plugins_config.get(plugin_name, {})
_divide_cols_list = current_plugin_conf.get('divide_columns', [])
divide_columns = { col: set() for col in _divide_cols_list }
# divide_columns

s3_snapshots = get_kdiff_snapshot_metadata_files_for_plugin(bucket_name, sidebar_plugin_param)
s3_snapshots_df = pd.DataFrame(s3_snapshots)
# s3_snapshots_df
# print(json.dumps(s3_snapshots, indent=2, default=str))



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

col1, col2, col3 = st.columns([4, 2, 1])

# -- WIDGET right-most column for view settings 

with col3:
    st.space(size="small")
    # popover = st.popover(":rainbow[View Options]", icon=":material/settings:",)  #  type='primary'
    popover = st.popover("", icon=":material/settings:",)  #  type='primary'
    row_height_slider = popover.slider("Row Height", 10, 120, 20, key="row_height")
    table_height_slider = popover.slider("Table Height", 300, 2000, 300, key="table_height")


# -- SIDEBAR sp connection 
dividers = selected_snapshot.get('dividers', {})
# st.markdown('#### dividers found')
connection_values = dividers.get('sp_connection_name', [])
sp_connection_selected = st.sidebar.radio('**SP Connection**',options=connection_values,)


# -- WIDGET object kinds
# snp_filenames = [snp['filename'] for snp in snapshot_data_list]
snp_filenames = set(selected_snapshot['checksums'])
# with col1:
# st.header("A cat")
selected_filenames = col1.multiselect(
    "Objects",
    snp_filenames,
    default=snp_filenames,
    # width="stretch",
    # width=600,
    format_func=lambda s: s.replace(f"{sidebar_plugin_param}_", "").replace(".csv", "")
)
if not selected_filenames:
    st.warning("No Objects are selected, :rainbow[what do you want me to do?]")
# -- SIDEBAR transpose 
transpose_on = st.sidebar.toggle("Transpose Tables")

if transpose_on:
    st.write("transpose_on Feature activated!")


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


def aaaaaa(dataframe, filename, filepath, plugin_name, table_name) -> Dict:

    _default_hide_cols = current_plugin_conf.get('_default', {}).get('hide_columns', [])
    table_config = current_plugin_conf.get('tables', {}).get(table_name, {})
    hide_columns = table_config.get('hide_columns', [])
    hide_columns.extend(_default_hide_cols)
    # hide_columns
    # table_config

    if table_config:
        if hide_columns:
            dataframe = dataframe.drop(columns=hide_columns, errors='ignore')

        show_first_cols = table_config.get('show_first', [])
        
        all_cols = list(dataframe.columns)
        show_first_cols = [c for c in show_first_cols if c in all_cols]

        if show_first_cols:
            display_cols = show_first_cols
            remaining_cols = [c for c in all_cols if c not in show_first_cols]
            display_cols.extend(remaining_cols)
            dataframe = dataframe[display_cols]
            

    # dataframe.columns.name =  # label above columns
    # dataframe.index.name = sidebar_plugin_param + '/' + table_name 
    # divide_columns
    
    if transpose_on:
        dataframe = dataframe.T

    r = {
        'filepath': filepath,
        'filename': filename,
        'dataframe': dataframe,
        'tablename': table_name,
    }
    return r 
    pass


def get_snapshot_data(snapshot: pd.DataFrame) -> List[Dict]:
    # snapshot
    snapshot_dict = snapshot.to_dict()
    # snapshot_dict
    sync_kdiff_snapshot_to_local_filesystem(snapshot_dict)
    
    checksums = snapshot_dict['checksums']
    snp_path = Path(local_dir_for_s3_sync) / snapshot_dict['snapshot_dir']
    filenames = set(checksums.keys())
    
    # _default_hide_cols = current_plugin_conf.get('_default', {}).get('hide_columns', [])
    # table_config = current_plugin_conf.get('tables', {}).get(table_name, {})
    # hide_columns = table_config.get('hide_columns', [])
    # hide_columns.extend(_default_hide_cols)
    
    r = []
    # checksums = selected_snapshot['checksums']
    # filenames = set(checksums.keys())
    for filename in selected_filenames:
        _file_path = snp_path / filename
        table_name = filename.replace(f"{plugin_name}_", "").replace(".csv", "")
        dataframe = csv_to_dataclass(_file_path, {})
        if not dataframe.empty:
            for col in _divide_cols_list:
                if col in dataframe.columns: 
                    for uniq_val in dataframe[col].dropna().unique().tolist():
                        divide_columns[col].add(uniq_val)  
            df_dict = {
                'filepath': _file_path,
                'filename': filename,
                'dataframe': dataframe,
                'tablename': table_name,
            }
            r.append(df_dict)
    return r


# ------------ SCRIPT STARTS HERE
st.markdown(f"#### plugin:{plugin_name} connection:{sp_connection_selected} namespace:{1}")

snapshot_data_list = get_snapshot_data(selected_snapshot)
# TODO: if json-array: kind:List,version:v1,items:[] format to better table show

# -- FILTER dataframes by sp_connection_name (context)
if sp_connection_selected:
    for snp_df_item in snapshot_data_list:
        # snp_df_item
        table_name = snp_df_item['tablename']
        snp_df = snp_df_item['dataframe']
        new_snp_df = snp_df[snp_df['sp_connection_name'] == sp_connection_selected]
        snp_df_item['dataframe'] = new_snp_df

    
# -- ADD divider widgets(context, account, region etc.)
divider_widgets={}
for col_name, div_options in divide_columns.items():
    
    # abcddas = col2.radio(
    abcddas = col2.multiselect(
        col_name.capitalize(),
        # divide_columns[0],
        options=div_options,
        default=div_options,
        # key=inp_param_name,
        # format_func=lambda option: option_map[option],
        # selection_mode="single",
    )
    divider_widgets[col_name] = abcddas
    # divide_columns[col_name]['widget']=abcddas


# -- FILTER dataframes by divider_columns (context)
if divider_widgets:
    
    for col_name in divider_widgets.keys():
        _allowed_values =  divider_widgets[col_name]
        # 'widget', col_name, _allowed_values
        
        if selected_filenames and (not _allowed_values):
            st.warning(f"No **{col_name}** selected — showing **non-{col_name}'d** objects ")
        
        for snp_df_item in snapshot_data_list:
            snp_df = snp_df_item['dataframe']
            if col_name in snp_df.columns:
                new_snp_df = snp_df[snp_df[col_name].isin(_allowed_values)]
                # new_snp_df = snp_df[snp_df['sp_connection_name'] == sp_connection_selected]
                snp_df_item['dataframe'] = new_snp_df
                
    # for snp_df_item in snapshot_data_list:
    #     # snp_df_item
    #     table_name = snp_df_item['tablename']
    #     snp_df = snp_df_item['dataframe']
    #     new_snp_df = snp_df[snp_df['sp_connection_name'] == sp_connection_selected]
    #     snp_df_item['dataframe'] = new_snp_df
        
    


# -- RENDER the dataframe
for snp_df_item in snapshot_data_list:
    # snp_df_item
    table_name = snp_df_item['tablename']
    snp_df = snp_df_item['dataframe']
    # snp_df.style.format(lambda x: json.dumps(x, indent=2) if isinstance(x, (list, dict)) else x)

    # st.markdown(f"###### {table_name}")
    if not snp_df.empty:
        st.markdown(f"###### {table_name}")
        
        st.dataframe(
            snp_df,
            row_height=row_height_slider,
            height=table_height_slider if (table_height_slider / row_height_slider) < len(snp_df) else 'auto',
            # width='stretch',
            # width=table_width_slider,
        )
    else:
        # st.markdown(f"###### {table_name} (n/a in selected {', '.join(list(divide_columns.keys()))})")
        # st.markdown(f"###### {table_name} (n/a)")
        pass

# snapshot_dataframes