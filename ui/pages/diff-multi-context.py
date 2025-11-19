
import streamlit as st
st.set_page_config(layout="wide")

from typing import List, DefaultDict, Dict
from datetime import datetime
from config import boto3_session, bucket_name, ui_config, snapshots_s3_prefix, main_diff_dir, local_dir_for_s3_sync
from storage import *
from pathlib import Path
import json
import pandas as pd
from misc import *
from diff_csv import qsv_diff_different_files
from io import StringIO
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
plugin_unique_column = current_plugin_conf.get('diffs', {}).get('unique_column', False)
divide_columns = { col: set() for col in _divide_cols_list }
# divide_columns

s3_snapshots = get_kdiff_snapshot_metadata_files_for_plugin(bucket_name, sidebar_plugin_param)
# s3_snapshots =  s3_snapshots
s3_snapshots_df = pd.DataFrame(s3_snapshots).sort_values('timestampObj', ascending=False)
s3_snapshots_df
# print(json.dumps(s3_snapshots, indent=2, default=str))



# def set_sidebar_params():
#     # ---- SIDEBAR PARAMS ----
#     # st.markdown("# set_sidebar_params")
#     # snapshot_list
#     # s3_snapshots
#     if not s3_snapshots:
#         {"failed": "s3_snapshots empty", "s3_snapshots": s3_snapshots}
#         st.sidebar.markdown(f"No snapshots are found")
#         st.exception(f"No snapshots are found for {sidebar_plugin_param}")
            
#     # Extract date and time columns
#     s3_snapshots_df["date"] = s3_snapshots_df["timestampObj"].dt.date
#     s3_snapshots_df["time"] = s3_snapshots_df["timestampObj"].dt.strftime("%H:%M:%S")

#     # --- Sidebar DATE selector ---
#     unique_dates = sorted(s3_snapshots_df["date"].unique())

#     # unique_dates

#     selected_date = st.sidebar.date_input(
#         "Select a snapshot date",
#         value=unique_dates[-1],            # default = latest date
#         min_value=min(unique_dates),
#         max_value=max(unique_dates),
#     )

#     # --- Filter snapshots for the selected date ---
#     df_for_date = s3_snapshots_df[s3_snapshots_df["date"] == selected_date]

#     # Show times belonging to that date
#     time_options = df_for_date["time"].tolist()

#     selected_time = st.sidebar.selectbox(
#         "Select a snapshot time",
#         options=time_options,
#         key="selected_time"
#     )

#     # --- Find the selected snapshot row ---
#     selected_snapshot = df_for_date[df_for_date["time"] == selected_time].iloc[0]
#     return selected_snapshot


# selected_snapshot = set_sidebar_params()

col1, col2, col3 = st.columns([4, 2, 1],border=True)
# -- WIDGET right-most column for view settings 
with col3:
    st.space(size="small")
    # popover = st.popover(":rainbow[View Options]", icon=":material/settings:",)  #  type='primary'
    popover = st.popover("", icon=":material/settings:",)  #  type='primary'
    row_height_slider = popover.slider("Row Height", 10, 120, 20, key="row_height")
    table_height_slider = popover.slider("Table Height", 300, 2000, 300, key="table_height")


# # -- SIDEBAR sp connection 
# dividers = selected_snapshot.get('dividers', {})
# # st.markdown('#### dividers found')
# connection_values = dividers.get('sp_connection_name', [])
# sp_connection_selected = st.sidebar.radio('**SP Connection**',options=connection_values,)


# -- WIDGET object kinds
# snp_filenames = [snp['filename'] for snp in snapshot_data_list]
# snp_filenames = set(selected_snapshot['checksums'])
# # with col1:
# # st.header("A cat")
# selected_filenames = col1.multiselect(
#     "Objects",
#     snp_filenames,
#     default=snp_filenames,
#     # width="stretch",
#     # width=600,
#     format_func=lambda s: s.replace(f"{sidebar_plugin_param}_", "").replace(".csv", "")
# )
# if not selected_filenames:
#     st.warning("No Objects are selected, :rainbow[what do you want me to do?]")

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
    
    # if transpose_on:
    #     dataframe = dataframe.T

    r = {
        'filepath': filepath,
        'filename': filename,
        'dataframe': dataframe,
        'tablename': table_name,
    }
    return r 
    pass


def get_snapshot_data(snapshot: pd.DataFrame, selected_filenames: List[str]) -> List[Dict]:
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




def run_qsv_diff_for_two_snapshots(snpA, snpB, changed_filenames,sp_connection_name):
    """ Generates *.diff.csv files"""
    _diff_id = hash_snapshots_for_diff_id(snpA['snapshot_dir'], snpB['snapshot_dir'])
    snp_A_path = Path(local_dir_for_s3_sync) / snpA['snapshot_dir']
    snp_B_path = Path(local_dir_for_s3_sync) / snpB['snapshot_dir']
    _active_diff_path = Path(main_diff_dir) / _diff_id
   
    if not _active_diff_path.exists():
        _active_diff_path.mkdir(parents=True, exist_ok=True) # to gen files with qsv.sh
        # st.toast(f"Diff Folder created: {_active_diff_path} Complete", icon="", duration="short")
        f"Diff Folder created: {_active_diff_path} Complete"

    r_list = [] 
    # st.markdown("### HERHEHERE")
    for ch_filename in changed_filenames:
        snp_A_ch_filepath = snp_A_path / ch_filename
        snp_B_ch_filepath = snp_B_path / ch_filename
        _ch_filename_diff_csv = f"{str(Path(ch_filename).stem)}.diff.csv"
        _ch_filename_diff_csv_save_path = _active_diff_path / _ch_filename_diff_csv
        # _ch_filename_diff_csv
        # _ch_filename_diff_csv_save_path
        out = qsv_diff_different_files(snp_A_ch_filepath, snp_B_ch_filepath, plugin_unique_column, sp_connection_name)
        # out
        if not out:
            continue
        diff_df = pd.read_csv(StringIO(out))
        # df = pd.read_csv(StringIO(csv_data))
        # out
        if diff_df.empty:
            continue
        oo = {
            'active_diff_path': _active_diff_path,
            'diff_filename': _ch_filename_diff_csv,
            'diff_csv_str': out,
            'diff_df': diff_df,
            'diff_id':_diff_id,
            'filename':ch_filename,
        }
        r_list.append(oo)
    return r_list




def render_common_files_as_diff_output(snpA, snpB, filenames, id_column, sp_connection_name):
    st.markdown("## ccccccccccc")
    # read csv files 
    _diff_id = hash_snapshots_for_diff_id(snpA['snapshot_dir'], snpB['snapshot_dir'])
    snp_A_path = Path(local_dir_for_s3_sync) / snpA['snapshot_dir']
    snp_B_path = Path(local_dir_for_s3_sync) / snpB['snapshot_dir']
    _active_diff_path = Path(main_diff_dir) / _diff_id  # actively used local dir for gen. .diff.csv files  
    objj = {}
    
    
    for filename in filenames:
        st.markdown(f"### {filename}")
        
        _file_path_A = snp_A_path / filename
        _file_path_B = snp_B_path / filename
        _file_path_diff_csv = _active_diff_path / f"{str(Path(filename).stem)}.diff.csv"
        
        if not _file_path_A.exists():
            st.error(f"ERROR: csv file {_file_path_A} does not exists")
        if not _file_path_B.exists():
            st.error(f"ERROR: csv file {_file_path_B} does not exists")
        if not _file_path_diff_csv.exists():
            st.error(f"ERROR: csv file {_file_path_diff_csv} does not exists")
        # _file_path_A, _file_path_B, _file_path_diff_csv
        # st.markdown(styled_df.to_html(escape=False), unsafe_allow_html=True)


        raw_diff_df = csv_to_dataclass(_file_path_diff_csv, {})
        A_df = csv_to_dataclass(_file_path_A, {})
        B_df = csv_to_dataclass(_file_path_B, {})
        # A_df
        # B_df
        if not raw_diff_df.empty: 
            raw_diff_df
        # result = parse_diff_dataframe(raw_diff_df, A_df, B_df)
        
        # if not result['added'].empty:
        #     result['added']
        
        # modified_df = result['modified']
        
        # if not modified_df.empty:
        #     st.markdown(f"### {filename}")
        #     "=== MODIFIED ==="
        #     modified_df
            
        
        # 1. 
        
        
        
        # # result
        # st.markdown(f"### {filename}")
        # if not result['modified'].empty:
        #     "=== MODIFIED ==="
        #     result['modified']
        # if not result['added'].empty:
        #     "\n=== ADDED ==="
        #     result['added']
        # if not result['removed'].empty:
        #     "\n=== REMOVED ==="
        #     result['removed']
        # objj[filename] = {
        #     "filename": filename,
        #     "filepath_A": _file_path_A,
        #     "filepath_B": _file_path_B,
        #     "active_diff_path": _active_diff_path,
        #     "diff_df": raw_diff_df,
        #     "A_df": A_df,
        #     "B_df": B_df,
        #     "result":result
        # }
        
        # NEW_KIND_OF_OBJ:: added files, from B, show all values
        # DELETED_KIND_OF_OBJ:: 
        
        # SAME KIND::
        #   ADDED ENTRY:: 
        #   DELETED ENTRY:: 
        #   CHANGED ENTRY::
        #.   - 2 rows 
        
        
    return objj
    pass




# def diff_two_snapshots(snpA, snpB, sp_connection_name):
#     # x = render_common_files_as_diff_output(snpA, snpB, list(common_files), 'uid',sp_connection_name)
#     # # x


# -- SnpA and SnpB widgets




# s3_snapshots_df

inp_col1, inp_col2 = st.columns(2,border=True)

_selectable_dates = s3_snapshots_df['display_date'].dropna().unique().tolist()

with inp_col2:

    _selectable_dates_snp_B = s3_snapshots_df['display_date'].dropna().unique().tolist()
    # _selectable_dates_snp_B
    #  dataframe[col]
    snp_B_date = st.selectbox(
        "SnpB Date",
        _selectable_dates,
    )
    # select the rows where 'display_date' == snp_B_date
    
with inp_col1:
    # _selectable_dates_snp_A = s3_snapshots_df['display_date'].dropna().unique().tolist()
    # _selectable_dates_snp_A
    #  dataframe[col]
    snp_A_date = st.selectbox(
        "SnpA Date",
        _selectable_dates,
        index=1 if len(_selectable_dates)>1 else 0,
    )
    # select the rows where 'display_date' == snp_A_date
    
    
with inp_col1:
    df_for_date = s3_snapshots_df[
        s3_snapshots_df['display_date'] == snp_A_date
    ]
    # df_for_date
    _selecteble_times_A = df_for_date['display_time'].dropna().unique().tolist()
    # _selecteble_times_A
    snp_A_time = st.selectbox(
        "SnpA times",
        _selecteble_times_A,
        index=1 if (snp_A_date==snp_B_date) and len(_selecteble_times_A)>1 else 0,
    )
    snp_A_date, snp_A_time

with inp_col2:

    df_for_date = s3_snapshots_df[
        s3_snapshots_df['display_date'] == snp_B_date
    ]
    # df_for_date
    _selecteble_times_B = df_for_date['display_time'].dropna().unique().tolist()
    # _selecteble_times_B
    snp_B_time = st.selectbox(
        "SnpB times",
        _selecteble_times_B,
    )


    snp_B_date, snp_B_time


snp_A = s3_snapshots_df[
    (s3_snapshots_df['display_date'] == snp_A_date) &
    (s3_snapshots_df['display_time'] == snp_A_time)
].iloc[0].to_dict()
snp_B = s3_snapshots_df[
    (s3_snapshots_df['display_date'] == snp_B_date) &
    (s3_snapshots_df['display_time'] == snp_B_time)
].iloc[0].to_dict()

# -- SIDEBAR sp connection 
dividersA = snp_A.get('dividers', {}).get('sp_connection_name', [])
dividersB = snp_B.get('dividers', {}).get('sp_connection_name', [])
common_sp_conn_names = list(set(dividersA) & set(dividersB))
if not common_sp_conn_names:
    st.warning(f'These snapshots don\'t have any common SP Connection — left: "{', '.join(dividersA)}" right: "{', '.join(dividersB)}"')
# st.markdown('#### dividers found')
# connection_values = dividers.get('sp_connection_name', [])
sp_connection_selected = st.sidebar.radio('**SP Connection**',options=common_sp_conn_names,)



# -- SIDEBAR auto_press_button 
auto_press_button = st.sidebar.toggle("Always Diff")

if st.button("DIFF BABY DIFF", type='primary', width='stretch') or auto_press_button:
    if not (snp_A_date and snp_A_time) and (snp_B_date and snp_B_time):
        st.error("Please select two snapshots to compare.")
    
    snp_A = s3_snapshots_df[
        (s3_snapshots_df['display_date'] == snp_A_date) &
        (s3_snapshots_df['display_time'] == snp_A_time)
    ].iloc[0].to_dict()
    snp_B = s3_snapshots_df[
        (s3_snapshots_df['display_date'] == snp_B_date) &
        (s3_snapshots_df['display_time'] == snp_B_time)
    ].iloc[0].to_dict()


    # -- GOT THE 2 SNAPSHOT DICTS!

    # snp_A
    # snp_B

    sync_kdiff_snapshot_to_local_filesystem(snp_A)
    sync_kdiff_snapshot_to_local_filesystem(snp_B)
    
    st.markdown('# diff_two_snapshots')
    # snpA
    # st.markdown('---')
    # snpB
    # new_objects, deleted_objects, changed_objects = compare_checksums_names(checksums_A, checksums_B)
    # snpA
    checksums_A = snp_A['checksums']
    checksums_B = snp_B['checksums']

    filenames_A = set(checksums_A.keys())
    filenames_B = set(checksums_B.keys())

    # Files that exist in both A and B (potentially changed)
    common_files = filenames_A & filenames_B
    # Files deleted (in A but not in B)
    deleted_files = filenames_A - filenames_B
    # Files added (in B but not in A)
    added_files = filenames_B - filenames_A
    # Files changed (exist in both but with different checksums)
    changed_files = {f for f in common_files if checksums_A[f] != checksums_B[f]}
    # Files unchanged (exist in both with same checksums)
    unchanged_files = {f for f in common_files if checksums_A[f] == checksums_B[f]}

    # "deleted_files", deleted_files
    # "added_files", added_files
    # "changed_files", changed_files
    # "unchanged_files", unchanged_files
    st.markdown('#### common_files ')
    common_files
    st.markdown('#### added_files ')
    added_files
    st.markdown('#### deleted_files ')
    deleted_files

    st.markdown('---')
    # sp_connection_name = "kubernetes_kind_kinder"

    diff_csv_outputs = run_qsv_diff_for_two_snapshots(snp_A, snp_B, list(common_files), sp_connection_selected)
    for d in diff_csv_outputs:
        st.markdown(f'#### {d['filename']}')
        d['diff_df']

    # snp_A
    # snp_B


 


# st.markdown(f"#### plugin:{plugin_name} connection:{sp_connection_selected} namespace:{1}")

# snapshot_data_list = get_snapshot_data(selected_snapshot)
# # TODO: if json-array: kind:List,version:v1,items:[] format to better table show

# # -- ADD divider widgets(context, account, region etc.)
# divider_widgets={}
# for col_name, div_options in divide_columns.items():
    
#     # abcddas = col2.radio(
#     abcddas = col2.multiselect(
#         col_name.capitalize(),
#         # divide_columns[0],
#         options=div_options,
#         default=div_options,
#         # key=inp_param_name,
#         # format_func=lambda option: option_map[option],
#         # selection_mode="single",
#     )
#     divider_widgets[col_name] = abcddas
#     # divide_columns[col_name]['widget']=abcddas


# # -- FILTER dataframes by divider_columns (context)
# if divider_widgets:
    
#     for col_name in divider_widgets.keys():
#         _allowed_values =  divider_widgets[col_name]
#         # 'widget', col_name, _allowed_values
        
#         if selected_filenames and (not _allowed_values):
#             st.warning(f"No **{col_name}** selected — showing **non-{col_name}'d** objects ")
        
#         for snp_df_item in snapshot_data_list:
#             snp_df = snp_df_item['dataframe']
#             if col_name in snp_df.columns:
#                 new_snp_df = snp_df[snp_df[col_name].isin(_allowed_values)]
#                 # new_snp_df = snp_df[snp_df['sp_connection_name'] == sp_connection_selected]
#                 snp_df_item['dataframe'] = new_snp_df
                
#     # for snp_df_item in snapshot_data_list:
#     #     # snp_df_item
#     #     table_name = snp_df_item['tablename']
#     #     snp_df = snp_df_item['dataframe']
#     #     new_snp_df = snp_df[snp_df['sp_connection_name'] == sp_connection_selected]
#     #     snp_df_item['dataframe'] = new_snp_df
        
    


# # -- RENDER the dataframe
# for snp_df_item in snapshot_data_list:
#     # snp_df_item
#     table_name = snp_df_item['tablename']
#     snp_df = snp_df_item['dataframe']
#     # snp_df.style.format(lambda x: json.dumps(x, indent=2) if isinstance(x, (list, dict)) else x)

#     # st.markdown(f"###### {table_name}")
#     if not snp_df.empty:
#         st.markdown(f"###### {table_name}")
        
#         st.dataframe(
#             snp_df,
#             row_height=row_height_slider,
#             height=table_height_slider if (table_height_slider / row_height_slider) < len(snp_df) else 'auto',
#             # width='stretch',
#             # width=table_width_slider,
#         )
#     else:
#         # st.markdown(f"###### {table_name} (n/a in selected {', '.join(list(divide_columns.keys()))})")
#         # st.markdown(f"###### {table_name} (n/a)")
#         pass

# # snapshot_dataframes