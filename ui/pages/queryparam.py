from datetime import datetime
import streamlit as st
from storage import get_kdiff_snapshot_metadata_files
import pandas as pd
from config import bucket_name, main_diff_dir, local_dir_for_s3_sync
from misc import *
from diff_csv import qsv_diff_different_files
from typing import List, Dict
from s3_and_local_files import run_aws_cli_sync
# import yaml

USER_TIMEZONE = st.context.timezone
USER_LOCALE = st.context.locale

# st.markdown("# Query Param")
# st.sidebar.markdown("### Query Param")
# st.markdown("---")
# st.context



def main():
    # -- init vars --
    s3_snapshots = get_kdiff_snapshot_metadata_files(bucket_name)
    s3_snapshots_by_names = {_['snapshot_name']:_ for _ in s3_snapshots}
    s3_snapshot_names = tuple(s3_snapshots_by_names.keys())
    
    # -- VALIDATE QUERY PARAMETERS --
    _require_query_params = ("snapshot-a","snapshot-b")
    _params_valid, _err_msg = ensure_query_params_are_passed(st.query_params, _require_query_params)
    
    if not _params_valid:
        st.warning("http://localhost:8501/queryparam?snapshot-a=kdiff-snapshot-2025-11-07--10-24&snapshot-b=kdiff-snapshot-2025-11-07--10-28") # TODO Delete later
        st.error(f"This page requires Query Parameters. Error: {_err_msg}")
        st.stop() 
    # ------------------------------------------------------------------------

    # -- use the snapshot query parameters
    snp_source = st.query_params['snapshot-a']
    snp_target = st.query_params['snapshot-b']
    "snp_source", snp_source, "---", "snp_target", snp_target
    # -- Validate the Snapshots exist in S3 -- 
    if (snp_source not in s3_snapshot_names) or (snp_target not in s3_snapshot_names):
        if snp_source not in s3_snapshot_names:
            st.error(f"Snapshot NOT FOUND on S3 Error: {st.query_params['snapshot-a']}")
        if snp_target not in s3_snapshot_names:
            st.error(f"Snapshot NOT FOUND on S3 Error: {st.query_params['snapshot-b']}")
        st.stop()
    # ------------------------------------------------------------------------
    # 
    st.markdown('---')
    diff_two_snapshots(s3_snapshots_by_names[snp_source], s3_snapshots_by_names[snp_target])
    
    
    # 1. check the checksums, get new,deleted,changed
    # 2. for changed ones, implement diff 
    
    # s3_snapshots
    snapshot_list = []
    

def sync_kdiff_snapshot_to_local(snp_obj):
    # st.markdown("# sync_kdiff_snapshot_to_local")
    # snp_obj
    snapshot_name = snp_obj['snapshot_name']
    snapshot_dir = snp_obj['snapshot_dir']
    "snapshot_name", snapshot_name, "  --  ","snapshot_dir", snapshot_dir
    local_dir_for_s3_sync_path = Path(local_dir_for_s3_sync)
    active_snapshot_sync_path = local_dir_for_s3_sync_path / snapshot_dir
    "active_snapshot_sync_path", active_snapshot_sync_path 
    if not active_snapshot_sync_path.exists():
        "making a dir for ", active_snapshot_sync_path
        active_snapshot_sync_path.mkdir(parents=True, exist_ok=True)
    st.toast(f"AWS S3 downloading {snapshot_name}...", icon=None, duration="short")
    
    # with st.status("Downloading data..."):
    #     st.write("Searching for data...")
    # aws_sync_result = run_aws_cli_sync(bucket_name, snapshot_dir, str(active_snapshot_sync_path), include_pattern='*.csv')
    aws_sync_result = run_aws_cli_sync(bucket_name, snapshot_dir, str(active_snapshot_sync_path))
    if aws_sync_result:
        st.toast(f"AWS S3 download {snapshot_name} Complete", icon="🎉", duration="short")
    else:
        st.error(f"Failed to sync AWS to Local: {bucket_name}, {snapshot_dir}, {str(active_snapshot_sync_path)}")

# def get_data_classes(snpA, snpB):
#     table_structure_json_path_list = [
#         Path(local_dir_for_s3_sync) / snpA['snapshot_dir'] / 'tables.structure.json',
#         Path(local_dir_for_s3_sync) / snpB['snapshot_dir'] / 'tables.structure.json'
#     ]
#     # tables = get_data_tables_from_multiple_schemas(table_structure_json_path_list)
#     # print("-*--**-*-09889-**-*-*-*-*")
#     # print(json.dumps(tables, indent=2, default=str))
#     return tables

def generate_qsv_diff_for_file_list(snpA, snpB, changed_filenames):
    """ Generates *.diff.csv files"""
    # st.markdown("# ejrere")
    # snpA['snapshot_dir']
    # snpB['snapshot_dir']
    _diff_id = hash_snapshots_for_diff_id(snpA['snapshot_dir'], snpB['snapshot_dir'])

    st.markdown("# diff id: "+_diff_id)
    snp_A_path = Path(local_dir_for_s3_sync) / snpA['snapshot_dir']
    snp_B_path = Path(local_dir_for_s3_sync) / snpB['snapshot_dir']

    _active_diff_path = Path(main_diff_dir) / _diff_id
   
    if not _active_diff_path.exists():
        _active_diff_path.mkdir(parents=True, exist_ok=True) # to gen files with qsv.sh
        # st.toast(f"Diff Folder created: {_active_diff_path} Complete", icon="", duration="short")
        f"Diff Folder created: {_active_diff_path} Complete"

    tables = get_data_classes(snpA,snpB)

    r_list = [] 
    # st.markdown("### HERHEHERE")
    for ch_filename in changed_filenames:
        snp_A_ch_filepath = snp_A_path / ch_filename
        snp_B_ch_filepath = snp_B_path / ch_filename
        _ch_filename_diff_csv = f"{str(Path(ch_filename).stem)}.diff.csv"
        _ch_filename_diff_csv_save_path = _active_diff_path / _ch_filename_diff_csv
        # _ch_filename_diff_csv
        # _ch_filename_diff_csv_save_path
        out = qsv_diff_different_files(snp_A_ch_filepath, snp_B_ch_filepath, _ch_filename_diff_csv_save_path)
        # out
        
        r_list.append(out)
    return r_list


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


def render_common_files_as_diff_output(snpA, snpB, filenames):
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
        result = parse_diff_dataframe(raw_diff_df, A_df, B_df)
        
        # if not result['added'].empty:
        #     result['added']
        
        modified_df = result['modified']
        
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

# def parse_diff_dataframe(diff_df: pd.DataFrame, df_A, df_B, unique_cols: List[str] = ['namespace', 'name']) -> Dict[str, pd.DataFrame]:
def parse_diff_dataframe(diff_df: pd.DataFrame, df_A, df_B, unique_cols: List[str] = ['uid']) -> Dict[str, pd.DataFrame]:
    """
    Given a DataFrame produced by `qsv diff`, group modified rows (those having both '+' and '-'
    for the same unique_cols values) into separate sub-DataFrames.

    Returns:
        {
            "modified": pd.DataFrame(...),
            "added": pd.DataFrame(...),
            "removed": pd.DataFrame(...)
        }
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
    # modified_df = (
    #     diff_df[
    #         diff_df[unique_cols].apply(tuple, axis=1).isin(modified_keys)
    #     ]
    #     .query("diffresult == '+'")              # Keep only '+' rows
    #     .drop(columns='diffresult')              # Drop the diffresult column
    #     # .sort_values(unique_cols)                # Optional: sort by unique_cols
    #     .reset_index(drop=True)                  # Optional: clean up index
    # )
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
  
    # ----------------------------SEPARATE DF for EACH DIFF-----------------------------------------






    # st.markdown("##### 1---1----1---11")
    
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
            styled_print_df = print_df.style.apply(highlight_second_row, axis=0)
            
            styled_print_df
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    return {
        "modified_keys": modified_keys,
        "modified": modified_df.reset_index(drop=True),
        "added": added_df.reset_index(drop=True),
        "removed": removed_df.reset_index(drop=True),
    }



def diff_two_snapshots(snpA, snpB):
    st.markdown('# diff_two_snapshots')
    # snpA
    # st.markdown('---')
    # snpB
    # new_objects, deleted_objects, changed_objects = compare_checksums_names(checksums_A, checksums_B)
    
    checksums_A = snpA['metadata_json']['checksums']
    checksums_B = snpB['metadata_json']['checksums']
    
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
    # changed_objects
    # Download the snapshot A
    sync_kdiff_snapshot_to_local(snpA)
    # Download the snapshot B
    sync_kdiff_snapshot_to_local(snpB)
    # Generate .diff.csv files for the two
    a = generate_qsv_diff_for_file_list(snpA, snpB, common_files)
    # ccccccccccc(snpA, snpB, list(common_files)[:2])
    
    # create 
    x = render_common_files_as_diff_output(snpA, snpB, list(common_files))
    # x
    pass


if __name__ == '__main__':
    main()
    
