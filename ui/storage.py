from config import boto3_session, bucket_name, snapshots_s3_prefix, local_dir_for_s3_sync
from functools import lru_cache
from pathlib import Path
from io import BytesIO
import json
from datetime import datetime
from typing import Dict, List
from s3_and_local_files import run_aws_cli_sync
import streamlit as st

# Create an S3 client
s3_client = boto3_session.client("s3")
s3_resource = boto3_session.resource("s3")
bucket = s3_resource.Bucket(bucket_name)
metadata_filename = 'kdiff-snapshot.metadata.json'
s3_client

# from cachetools import TTLCache, cached

# cache = TTLCache(maxsize=100, ttl=30)  # ttl = 30 seconds

# @cached(cache)
# def slow_function(x):
#     print("Computing...")
#     return x * 2


def sync_kdiff_snapshot_to_local_filesystem(snp_obj: Dict):
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
    # with st.status("Downloading data..."):
    #     st.write("Searching for data...")
    # aws_sync_result = run_aws_cli_sync(bucket_name, snapshot_dir, str(active_snapshot_sync_path), include_pattern='*.csv')
    
    with st.status(f"Downloading the S3 {snapshot_dir} data...", expanded=False) as status:
        aws_sync_result = run_aws_cli_sync(bucket_name, snapshot_dir, str(active_snapshot_sync_path))
        if aws_sync_result:
            status.update(label=":green[Download complete!]", state="complete")
        else:
            status.update(label=f":red[Failed to sync AWS to Local: {bucket_name}, {snapshot_dir}, {str(active_snapshot_sync_path)}] ", state="error")
    return aws_sync_result

@lru_cache(maxsize=1)
def get_all_objects(bucket):
    """ Get all objects from the bucket. Results are cached. """
    all_objects = []
    paginator = s3_client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket):
        if 'Contents' in page:
            all_objects.extend(page['Contents'])
    
    return tuple(all_objects)  # Return tuple since lru_cache requires hashable types

def list_folders(bucket, prefix):
    if prefix and not prefix.endswith("/"):
        prefix += "/"  # Ensure prefix ends with "/"

    paginator = s3_client.get_paginator("list_objects_v2")
    folder_names = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix, Delimiter="/"):
        for cp in page.get("CommonPrefixes", []):
            folder = cp["Prefix"][len(prefix):].rstrip("/")
            folder_names.append(folder)

    return folder_names

def find_plugin_snapshot_metadata_files(bucket, plugin_name):
    actual_prefix = str(Path(snapshots_s3_prefix) / plugin_name )
    filename = metadata_filename
    paginator = s3_client.get_paginator("list_objects_v2")
    if actual_prefix and not actual_prefix.endswith("/"):
        actual_prefix += "/"
    print(bucket, actual_prefix)
    matches = []
    for page in paginator.paginate(Bucket=bucket, Prefix=actual_prefix):
        for obj in page.get("Contents", []):
            if obj["Key"].endswith(filename):
                matches.append(obj)

    return matches

def filter_files_by_name(bucket, filename):
    """ Filter objects by filename from cached bucket contents. """
    all_objects = get_all_objects(bucket)
    
    matching_files = [
        obj for obj in all_objects
        if obj['Key'].endswith(f'/{filename}') or obj['Key'] == filename
    ]
    
    return matching_files

def get_kdiff_snapshot_metadata_path_objs(bucket):
    files = filter_files_by_name(bucket, metadata_filename)
    path_objs = [ Path(f['Key']) for f in files ]
    return path_objs

def get_kdiff_snapshot_dirs(bucket):
    metadata_path_objs = get_kdiff_snapshot_metadata_path_objs(bucket)
    kdiff_snapshot_dirs = [ str(mp.parent) for mp in metadata_path_objs ]
    return kdiff_snapshot_dirs 

def get_kdiff_snapshot_metadata_files_for_plugin(bucket, plugin_name):
    # plugin_name is inner prefix 
    
    md_file_objects = find_plugin_snapshot_metadata_files(bucket, plugin_name)
    r = []
    for md_object in md_file_objects:
        md_path = Path(md_object['Key'])
        print("------------")
        print(md_path)
        file_obj = BytesIO()  # Create a BytesIO buffer
        # load and read the file on memory
        s3_client.download_fileobj(bucket, str(md_path), file_obj)
        file_obj.seek(0)  # Move cursor to the beginning of the buffer
        content = file_obj.read() 
        try:
            mjson = json.loads(content)
            snapshot_info = mjson.get("snapshotInfo", {})
            timestamp = snapshot_info.get("timestamp")
            timestamp_dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            entry = {
                'bucket': bucket, 
                'timestampObj': timestamp_dt,
                'filepath': str(md_path),
                'plugin_name': plugin_name,
                "display_date": f"{timestamp_dt.strftime('%Y-%m-%d')}",
                "display_time": f"{timestamp_dt.strftime('%H:%M:%S')}",
                "snapshot_dir": str(Path(md_path).parent),
                "snapshot_name": Path(md_path).parent.name,
                "remote_s3_prefix": f"s3://{bucket_name}/{snapshots_s3_prefix}/",
                "remote_s3_uri": f"s3://{bucket_name}/{snapshots_s3_prefix}/",
            } | mjson
            r.append(entry)
        except json.decoder.JSONDecodeError:
            # them file aint json
            pass
        del file_obj
    return r

def get_kdiff_snapshot_metadata_files(bucket):
    md_paths = get_kdiff_snapshot_metadata_path_objs(bucket)
    r = []
    for md_path in md_paths:
        file_obj = BytesIO()  # Create a BytesIO buffer
        # load and read the file on memory
        s3_client.download_fileobj(bucket, str(md_path), file_obj)
        file_obj.seek(0)  # Move cursor to the beginning of the buffer
        content = file_obj.read() 
        try:
            mjson = json.loads(content)
            r.append({
                'bucket': bucket, 
                "snapshot_dir": str(Path(md_path).parent),
                "snapshot_name": Path(md_path).parent.name,
                "remote_s3_prefix": f"s3://{bucket_name}/{snapshots_s3_prefix}/",
                "remote_s3_uri": f"s3://{bucket_name}/{snapshots_s3_prefix}/",
                'filepath': str(md_path),
                "metadata_json":mjson
            })
        except json.decoder.JSONDecodeError:
            # them file aint json
            pass
        
            
        del file_obj
    return r


def _get_all_object_summaries(bucket):
    object_summary_iterator = bucket.objects.page_size(count=250)
    _result = {
        "bucket": bucket.name
    }
    _keys = []
    for obj in object_summary_iterator:
        _keys.append(obj.key)
    _result['keys'] = _keys
    return _result
