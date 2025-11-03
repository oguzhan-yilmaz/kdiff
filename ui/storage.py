from config import boto3_session, bucket_name
from functools import lru_cache


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


def get_all_object_summaries(bucket):
    object_summary_iterator = bucket.objects.page_size(count=250)
    _result = {
        "bucket": bucket.name
    }
    _keys = []
    for obj in object_summary_iterator:
        _keys.append(obj.key)
    _result['keys'] = _keys
    return _result
