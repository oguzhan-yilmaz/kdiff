from config import boto3_session, bucket_name
from functools import lru_cache
from pathlib import Path
from io import BytesIO
import json

# Create an S3 client
s3_client = boto3_session.client("s3")
s3_resource = boto3_session.resource("s3")
bucket = s3_resource.Bucket(bucket_name)

s3_client




@lru_cache(maxsize=1)
def get_all_objects(bucket):
    """ Get all objects from the bucket. Results are cached. """
    all_objects = []
    paginator = s3_client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket):
        if 'Contents' in page:
            all_objects.extend(page['Contents'])
    
    return tuple(all_objects)  # Return tuple since lru_cache requires hashable types


def filter_files_by_name(bucket, filename):
    """ Filter objects by filename from cached bucket contents. """
    all_objects = get_all_objects(bucket)
    
    matching_files = [
        obj for obj in all_objects
        if obj['Key'].endswith(f'/{filename}') or obj['Key'] == filename
    ]
    
    return matching_files

def get_kdiff_snapshot_metadata_path_objs(bucket):
    metadata_filename = 'kdiff-snapshot.metadata.json'
    files = filter_files_by_name(bucket, metadata_filename)
    path_objs = [ Path(f['Key']) for f in files ]
    return path_objs

def get_kdiff_snapshot_dirs(bucket):
    metadata_path_objs = get_kdiff_snapshot_metadata_path_objs(bucket)
    kdiff_snapshot_dirs = [ str(mp.parent) for mp in metadata_path_objs ]
    return kdiff_snapshot_dirs 

def get_kdiff_snapshot_metadata_files(bucket):
    md_paths = get_kdiff_snapshot_metadata_path_objs(bucket)
    r = []
    for md_path in md_paths:
        file_obj = BytesIO()  # Create a BytesIO buffer
        # load and read the file on memory
        s3_client.download_fileobj(bucket, str(md_path), file_obj)
        file_obj.seek(0)  # Move cursor to the beginning of the buffer
        content = file_obj.read() 
        
        
        
        r.append({
            'bucket': bucket, 
            "snapshot_dir": str(Path(md_path).parent),
            "snapshot_name": Path(md_path).parent.name,
            'filepath': str(md_path),
            "metadata_json":json.loads(content)
        })
        
            
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
