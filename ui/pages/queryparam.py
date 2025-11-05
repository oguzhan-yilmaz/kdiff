from datetime import datetime
import streamlit as st
from storage import get_kdiff_snapshot_metadata_files
import pandas as pd
from config import bucket_name
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
    

def diff_two_snapshots(snpA, snpB):
    st.markdown('# diff_two_snapshots')
    snpA
    # st.markdown('---')
    # snpB
    new_objects, deleted_objects, changed_objects = compare_checksums_names(snpA['metadata_json']['checksums'], snpB['metadata_json']['checksums'])
    st.markdown('---')
    st.markdown('### new_objects')
    new_objects
    st.markdown('### deleted_objects')
    deleted_objects
    st.markdown('### changed_objects')
    [from_csv_get_kube_name(_) for _ in changed_objects]
    
    changed_objects
    
    for co in changed_objects[:1]:
        co
        bucket_name
        result = run_aws_cli_sync(bucket_name, snpA['snapshot_dir'], '/Users/ogair/tmp-kdiff-diff-dir', include_pattern='*.csv')
        result.stdout
    pass


if __name__ == '__main__':
    main()
    
