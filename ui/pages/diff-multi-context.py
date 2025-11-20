
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
from schema_types import get_table_data_types



s3_remote_available_plugins = list_folders(bucket_name, snapshots_s3_prefix)
sidebar_plugin_param = st.sidebar.radio(
        "Plugin Name",s3_remote_available_plugins,
        index=0,
        format_func=lambda a: f"**{a}**"
    )

# -- GET Plugin Config
plugin_name = sidebar_plugin_param
plugins_config = ui_config.get('plugins', {})
current_plugin_conf = plugins_config.get(plugin_name, {})
_divide_cols_list = current_plugin_conf.get('divide_columns', [])
plugin_unique_column = current_plugin_conf.get('diffs', {}).get('unique_column', False)
divide_columns = { col: set() for col in _divide_cols_list }
# divide_columns


# -- READ S3 bucket to get available snapshots for the plugin
s3_snapshots = get_kdiff_snapshot_metadata_files_for_plugin(bucket_name, sidebar_plugin_param)
# s3_snapshots =  s3_snapshots
s3_snapshots_df = pd.DataFrame(s3_snapshots).sort_values('timestampObj', ascending=False)
s3_snapshots_df
# print(json.dumps(s3_snapshots, indent=2, default=str))


# -- WIDGET right-most column for view settings 
col1, col2, col3 = st.columns([4, 2, 1],border=True)
with col3:
    st.space(size="small")
    # popover = st.popover(":rainbow[View Options]", icon=":material/settings:",)  #  type='primary'
    popover = st.popover("", icon=":material/settings:",)  #  type='primary'
    row_height_slider = popover.slider("Row Height", 10, 120, 20, key="row_height")
    table_height_slider = popover.slider("Table Height", 300, 2000, 300, key="table_height")


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
        df_A = csv_to_dataclass(snp_A_ch_filepath, {})
        df_B = csv_to_dataclass(snp_B_ch_filepath, {})
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
            'df_A': df_A,
            'df_B': df_B,
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







# -- WIDGETS date/time widgets for SnpA and SnpB 
inp_col1, inp_col2 = st.columns(2,border=True)

_selectable_dates = s3_snapshots_df['display_date'].dropna().unique().tolist()

with inp_col2:
    snp_B_date = st.selectbox(
        "SnpB Date",
        _selectable_dates,
    )
    
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
    _selecteble_times_A = df_for_date['display_time'].dropna().unique().tolist()
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
    _selecteble_times_B = df_for_date['display_time'].dropna().unique().tolist()
    snp_B_time = st.selectbox(
        "SnpB times",
        _selecteble_times_B,
    )


    snp_B_date, snp_B_time

# -- GET SNAPSHOT json objects for SnpA and SnpB 
snp_A = s3_snapshots_df[
    (s3_snapshots_df['display_date'] == snp_A_date) &
    (s3_snapshots_df['display_time'] == snp_A_time)
].iloc[0].to_dict()
snp_B = s3_snapshots_df[
    (s3_snapshots_df['display_date'] == snp_B_date) &
    (s3_snapshots_df['display_time'] == snp_B_time)
].iloc[0].to_dict()

# -- SIDEBAR WIDGET Steampipe Connection  
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
# ==============================================================================================================================================
# ==============================================================================================================================================
# ==============================================================================================================================================





# def parse_diff_dataframe(diff_df: pd.DataFrame, df_A, df_B, unique_cols: List[str] = ['namespace', 'name']) -> Dict[str, pd.DataFrame]:
def parse_diff_dataframe(diff_df: pd.DataFrame, df_A, df_B, unique_cols: List[str] = ['uid']) -> Dict[str, pd.DataFrame]:
    """
    Given a DataFrame produced by `qsv diff`, group modified rows (those having both '+' and '-'
    for the same unique_cols values) into separate sub-DataFrames.

    Returns:
        { "modified": pd.DataFrame(...), "added": pd.DataFrame(...), "removed": pd.DataFrame(...) }
    """
    if diff_df.empty:
        return {"modified": pd.DataFrame(), "added": pd.DataFrame(), "removed": pd.DataFrame()}

    # Validate required columns
    if 'diffresult' not in diff_df.columns:
        raise ValueError("Input DataFrame must include a 'diffresult' column ('+' or '-').")

    # Split by diff type
    added_df = diff_df[diff_df['diffresult'] == '+'].copy()
    removed_df = diff_df[diff_df['diffresult'] == '-'].copy()

    # Identify keys that exist in both added and removed (modified)
    added_keys = set(tuple(row) for row in added_df[unique_cols].itertuples(index=False, name=None))
    removed_keys = set(tuple(row) for row in removed_df[unique_cols].itertuples(index=False, name=None))
    modified_keys = added_keys & removed_keys
    # "modified_keys", modified_keys
    # Build DataFrame of modified entries (both versions)
    modified_df = diff_df[
        diff_df[unique_cols].apply(tuple, axis=1).isin(modified_keys)
    ].sort_values(unique_cols + ['diffresult'])
    modified_df = modified_df.query("diffresult == '+'").drop(columns='diffresult')
    # modified_df
    # Filter out modified rows from added/removed sets
    added_df = added_df[
        ~added_df[unique_cols].apply(tuple, axis=1).isin(modified_keys)
    ]
    removed_df = removed_df[
        ~removed_df[unique_cols].apply(tuple, axis=1).isin(modified_keys)
    ]
    
    added_df = added_df.drop(columns='diffresult') 
    removed_df = removed_df.drop(columns='diffresult') 

    # Style removed rows with red background
    return {
        "modified_keys": modified_keys,
        "modified": modified_df.reset_index(drop=True),
        "added": added_df.reset_index(drop=True),
        "removed": removed_df.reset_index(drop=True),
    }










# ==============================================================================================================================================
# ==============================================================================================================================================
# ==============================================================================================================================================

# def get_data_classes(snpA, snpB):
#     table_structure_json_path_list = [
#         Path(local_dir_for_s3_sync) / snpA['snapshot_dir'] / 'tables.structure.json',
#         Path(local_dir_for_s3_sync) / snpB['snapshot_dir'] / 'tables.structure.json'
#     ]
#     tables = get_data_tables_from_multiple_schemas(table_structure_json_path_list)
#     print("-*--**-*-09889-**-*-*-*-*")
#     # print(json.dumps(tables, indent=2, default=str))
#     return tables


if auto_press_button or st.button("DIFF BABY DIFF", type='primary', width='stretch'):
    if (not snp_A) and (not snp_B):
        st.error("Please select two snapshots to compare.")
        st.markdown('# aaa---aab--b--')

    # -- GOT THE 2 SNAPSHOT DICTS!

    # snp_A
    # snp_B
    # data_classes = get_data_classes(snp_A, snp_B)

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
        filename=d['filename']
        _name= str(Path(filename).stem)
        # data_classes
        # dis_data_class = data_classes.get(_name, False)
        # dis_data_class
        diff_df = d['diff_df']
        df_A =  d['df_A']
        df_B =  d['df_B']
        # diff_df
        # df_A
        # df_B
        parsed_dict = parse_diff_dataframe(diff_df, df_A, df_B, unique_cols=plugin_unique_column.split(',')) 
        modified_keys = parsed_dict['modified_keys']
        modified_df = parsed_dict['modified']
        added_df = parsed_dict['added']
        removed_df = parsed_dict['removed']
        
        
        dtypes = get_table_data_types('/Users/ogair/Projects/kdiff/kdiff-snapshots/data/kubernetes/kdiff-snp-2025-11-16--20-32/tables.structure.json')
        dtypes
    # schema_json = get_scheme_json_file('/Users/ogair/Projects/kdiff/kdiff-snapshots/data/kubernetes/kdiff-snp-2025-11-16--20-32/tables.structure.json')
    # print(json.dumps(schema_json, indent=2, default=str))

        
        
        st.markdown("---")
        
        # ----------------------------SHOW EM-----------------------------------------
        if not added_df.empty: 
            styled_added = added_df.style.set_properties(**{
                'background-color': '#d4edda',  # light green
                'color': 'black'
            })
            st.markdown("**Added::in-place**")
            styled_added
        if not removed_df.empty: 
            styled_removed = removed_df.style.set_properties(**{
                'background-color': '#f8d7da',  # light red
                'color': 'black'
            })
            st.markdown("**Removed::in-place**")
            styled_removed
        
        dfs=[]
        for idx, row in modified_df.iterrows():
            uid = row['uid']
            original_row = df_A[df_A['uid'] == uid].iloc[0]
            
            # "row", row
            # "original_row", original_row
            new_df = pd.DataFrame([original_row, row])
            new_df = new_df.reset_index(drop=True)  # Sets index to 0, 1
            # for col in new_df.select_dtypes(include=['object', 'string']):
            #     new_df[col] = new_df[col].fillna("")
            # new_df.loc[0] = new_df.loc[0].fillna("")
            # new_df.loc[1] = new_df.loc[1].fillna("") 
            dfs.append(new_df)
            
        # if not modified_df.empty: 
        #     sytled_modified = modified_df.style.set_properties(**{
        #         'background-color': "#5d55b1",  # light red
        #         'color': 'black'
        #     })
        #     sytled_modified
        # def highlight_second_row(col):
        #     styles = [''] * len(col)
        #     styles[1] = 'background-color: #5d55b1; color: black'
        #     return styles
        def highlight_second_row(col):
            styles = [''] * len(col)
            # Check if the second row exists and has a non-empty value
            if len(col) > 1 and col.iloc[1] not in [None, '', float('nan')]:
                styles[1] = 'background-color: #5d55b1; color: black'
            return styles
        st.markdown("**Changed::in-place**")
        for print_df in dfs:
            if not print_df.empty: 
                # styled_print_df = print_df.style.set_properties(
                #     subset=pd.IndexSlice[1:1, :],  # Row index 1 (2nd row), all columns
                #     **{
                #         'background-color': "#5d55b1",
                #         'color': 'black'
                #     }
                # )
                # styled_print_df = print_df.T.style.apply(highlight_second_row, axis=0)
                styled_print_df = print_df.style.apply(highlight_second_row, axis=0)
                
                styled_print_df
    


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