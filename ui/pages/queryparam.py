from datetime import datetime
import streamlit as st
from storage import get_kdiff_snapshot_metadata_files
import pandas as pd
from config import bucket_name, main_diff_dir, local_dir_for_s3_sync
from misc import *
from s3_and_local_files import run_aws_cli_sync
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
        st.warning("http://localhost:8501/queryparam?snapshot-a=kdiff-snapshot-2025-11-03--23-17&snapshot-b=kdiff-snapshot-2025-11-03--23-54") # TODO Delete later
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
    aws_sync_result = run_aws_cli_sync(bucket_name, snapshot_dir, str(active_snapshot_sync_path), include_pattern='*.csv')
    if aws_sync_result:
        st.toast(f"AWS S3 download {snapshot_name} Complete", icon="🎉", duration="short")
    else:
        st.error(f"Failed to sync AWS to Local: {bucket_name}, {snapshot_dir}, {str(active_snapshot_sync_path)}, include_pattern='*.csv'")


def aaaaaaa(snpA, snpB, changed_filenames):
    st.markdown("# ejrere")
    snpA['snapshot_dir']
    snpB['snapshot_dir']
    _diff_id = hash_snapshots_for_diff_id(snpA['snapshot_dir'], snpB['snapshot_dir'])

    st.markdown("# diff id: "+_diff_id)
    snp_A_path = Path(local_dir_for_s3_sync) / snpA['snapshot_dir']
    snp_B_path = Path(local_dir_for_s3_sync) / snpB['snapshot_dir']
    st.markdown("# sn path")

    snp_A_path
    snp_B_path
    local_dir_for_s3_sync
    _active_diff_path = Path(main_diff_dir) / _diff_id
   
    if not _active_diff_path.exists():
        _active_diff_path.mkdir(parents=True, exist_ok=True) # to gen files with qsv.sh
        # st.toast(f"Diff Folder created: {_active_diff_path} Complete", icon="", duration="short")
        f"Diff Folder created: {_active_diff_path} Complete"
    # create a tmp dir 
    _active_diff_path
    changed_filenames
    st.markdown("### HERHEHERE")
    for ch_filename in changed_filenames:
        snp_A_ch_filepath = snp_A_path / ch_filename
        snp_B_ch_filepath = snp_B_path / ch_filename
        _ch_filename_diff_csv = f"{str(Path(ch_filename).stem)}.diff.csv"
        _ch_filename_diff_csv_save_path = _active_diff_path / _ch_filename_diff_csv
        _ch_filename_diff_csv
        _ch_filename_diff_csv_save_path
        f"qsv diff --drop-equal-fields --key namespace,name --sort-columns namespace,name  {snp_A_ch_filepath} {snp_B_ch_filepath} > {_ch_filename_diff_csv_save_path}"

def diff_two_snapshots(snpA, snpB):
    st.markdown('# diff_two_snapshots')
    # snpA
    # st.markdown('---')
    # snpB
    new_objects, deleted_objects, changed_objects = compare_checksums_names(snpA['metadata_json']['checksums'], snpB['metadata_json']['checksums'])
    # st.markdown('---')
    # st.markdown('### new_objects')
    # new_objects
    # st.markdown('### deleted_objects')
    # deleted_objects
    # st.markdown('### changed_objects')
    # # [from_csv_get_kube_name(_) for _ in changed_objects]
    
    # changed_objects
    changed_filenames = changed_objects
    sync_kdiff_snapshot_to_local(snpA)
    sync_kdiff_snapshot_to_local(snpB)
    aaaaaaa(snpA, snpB, changed_filenames)
    
    for co in changed_objects[:1]:
        co

    pass


if __name__ == '__main__':
    main()
    
