from datetime import datetime
import streamlit as st
from storage import get_kdiff_snapshot_metadata_files
import pandas as pd
from config import bucket_name, main_diff_dir, local_dir_for_s3_sync
from misc import *
from diff_csv import qsv_diff_different_files
from typing import List, Dict
from s3_and_local_files import run_aws_cli_sync
from schema_types import get_data_tables_from_multiple_schemas
from st_aggrid import AgGrid, GridOptionsBuilder

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
    st.markdown("# sync_kdiff_snapshot_to_local")
    # snp_obj
    snapshot_name = snp_obj['snapshot_name']
    snapshot_dir = snp_obj['snapshot_dir']
    "snapshot_name", snapshot_name
    "snapshot_dir", snapshot_dir
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

def get_data_classes(snpA, snpB):
    table_structure_json_path_list = [
        Path(local_dir_for_s3_sync) / snpA['snapshot_dir'] / 'tables.structure.json',
        Path(local_dir_for_s3_sync) / snpB['snapshot_dir'] / 'tables.structure.json'
    ]
    tables = get_data_tables_from_multiple_schemas(table_structure_json_path_list)
    print("-*--**-*-09889-**-*-*-*-*")
    print(json.dumps(tables, indent=2, default=str))
    return tables

def generate_qsv_diff_for_file_list(snpA, snpB, changed_filenames):
    st.markdown("# ejrere")
    snpA['snapshot_dir']
    snpB['snapshot_dir']
    _diff_id = hash_snapshots_for_diff_id(snpA['snapshot_dir'], snpB['snapshot_dir'])

    st.markdown("# diff id: "+_diff_id)
    snp_A_path = Path(local_dir_for_s3_sync) / snpA['snapshot_dir']
    snp_B_path = Path(local_dir_for_s3_sync) / snpB['snapshot_dir']

    _active_diff_path = Path(main_diff_dir) / _diff_id
   
    if not _active_diff_path.exists():
        _active_diff_path.mkdir(parents=True, exist_ok=True) # to gen files with qsv.sh
        # st.toast(f"Diff Folder created: {_active_diff_path} Complete", icon="", duration="short")
        f"Diff Folder created: {_active_diff_path} Complete"
    # _active_diff_path
    # changed_filenames
    st.markdown("### DATA TABLES")

    tables = get_data_classes(snpA,snpB)
    tables
    st.markdown("### HERHEHERE")
    for ch_filename in changed_filenames:
        snp_A_ch_filepath = snp_A_path / ch_filename
        snp_B_ch_filepath = snp_B_path / ch_filename
        _ch_filename_diff_csv = f"{str(Path(ch_filename).stem)}.diff.csv"
        _ch_filename_diff_csv_save_path = _active_diff_path / _ch_filename_diff_csv
        # _ch_filename_diff_csv
        # _ch_filename_diff_csv_save_path
        # f"qsv diff --drop-equal-fields --key namespace,name --sort-columns namespace,name  {snp_A_ch_filepath} {snp_B_ch_filepath} > {_ch_filename_diff_csv_save_path}"
        out = qsv_diff_different_files(snp_A_ch_filepath, snp_B_ch_filepath, _ch_filename_diff_csv_save_path)
        # out
        
def csv_to_dataclass(csv_file_path: Path, dataclass_table: Dict):
    """
    Read CSV file and convert rows to dataclass instances
    """
    df = pd.read_csv(csv_file_path)
    
    # Convert each row to dataclass instance
    # instances = []
    # # for _, row in df.iterrows():
    # #     instance = dataclass_type(**row.to_dict())
    # #     instances.append(instance)
    
    # return instances
    return df

def test_multiline_table():
    # Create sample data with multi-line text
    data = {
        'Name': ['Alice', 'Bob', 'Charlie'],
        'Description': [
            'Line 1\nLine 2\nLine 3',
            'First line\nSecond line\nThird line\nFourth line',
            'Short\nText'
        ],
        'Status': ['Active\nVerified', 'Pending\nReview', 'Complete']
    }
    
    df = pd.DataFrame(data)
    
    # Set pandas to show full content
    pd.set_option('display.max_colwidth', None)
    pd.set_option('display.width', None)
    
    print(df)
    
    return df

# Run the test
def ccccccccccc(snpA, snpB, filenames):
    st.markdown("## ccccccccccc")
    # read csv files 
    _diff_id = hash_snapshots_for_diff_id(snpA['snapshot_dir'], snpB['snapshot_dir'])
    snp_A_path = Path(local_dir_for_s3_sync) / snpA['snapshot_dir']
    snp_B_path = Path(local_dir_for_s3_sync) / snpB['snapshot_dir']
    _active_diff_path = Path(main_diff_dir) / _diff_id

    # _diff_id
    # snp_A_path
    # snp_B_path
    # _active_diff_path
    # aaa = test_multiline_table()
    # AgGrid(aaa, fit_columns_on_grid_load=True)
    # AgGrid(aaa, height=500, fit_columns_on_grid_load=True)
    for filename in filenames:
        _file_path_A = snp_A_path / filename
        _file_path_B = snp_B_path / filename
        _file_path_diff_csv = _active_diff_path / f"{str(Path(filename).stem)}.diff.csv"
        
        if not _file_path_A.exists():
            st.error(f"ERROR: csv file {_file_path_A} does not exists")
        if not _file_path_B.exists():
            st.error(f"ERROR: csv file {_file_path_B} does not exists")
        if not _file_path_diff_csv.exists():
            st.error(f"ERROR: csv file {_file_path_diff_csv} does not exists")
        _file_path_A, _file_path_B, _file_path_diff_csv

        # st.markdown(styled_df.to_html(escape=False), unsafe_allow_html=True)
        diff_pd = csv_to_dataclass(_file_path_diff_csv, {})
        pd1 = csv_to_dataclass(_file_path_A, {})
        def pretty_json(val):
            if pd.isna(val) or val == '':
                return ''
            try:
                # Parse the JSON string first
                obj = json.loads(val)
                # Then format it nicely
                return json.dumps(obj, indent=2, ensure_ascii=False)
            except:
                return val

        pd1['tags'] = pd1['tags'].apply(pretty_json)
        styled_df = pd1.style.set_properties(subset=['uid'], **{
            'background-color': 'lightblue',
            'color': 'black',
            'font-weight': 'bold'
        })
        
        
        pd2 = csv_to_dataclass(_file_path_B, {})

        tab1, tab2, tab3 = st.tabs(["Diff", "SnapshotA", "SnapshotB"])

        with tab1:
            # st.header("A cat")
            diff_pd

        with tab2:
            # st.header("A dog")
            # styled_df
            pd1
        with tab3:
            # st.header("An owl")
            pd2
        # Display with full column width (optional)
        # pd1.set_option('display.max_colwidth', None)
        # pd1.set_option('display.width', None)
        # AgGrid(pd1)
        

        # AgGrid(pd2)
        # st.markdown(pd2.to_html(escape=False), unsafe_allow_html=True)
        
    st.markdown("---")
    
    pass

def diff_two_snapshots(snpA, snpB):
    st.markdown('# diff_two_snapshots')
    # snpA
    # st.markdown('---')
    # snpB
    
    checksums_A = snpA['metadata_json']['checksums']
    checksums_B = snpB['metadata_json']['checksums']
    new_objects, deleted_objects, changed_objects = compare_checksums_names(checksums_A, checksums_B)
    
    st.markdown('### aaabbbbccc ')
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
    "common_files", common_files
    
    
    # changed_objects
    sync_kdiff_snapshot_to_local(snpA)
    sync_kdiff_snapshot_to_local(snpB)
    generate_qsv_diff_for_file_list(snpA, snpB, common_files)
    # ccccccccccc(snpA, snpB, list(common_files)[:2])
    ccccccccccc(snpA, snpB, list(common_files))

    pass


if __name__ == '__main__':
    main()
    
