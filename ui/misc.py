from pathlib import Path
from config import boto3_session, bucket_name
import json
from functools import lru_cache


# from io import BytesIO
# 
# # Create an S3 client
# s3_client = boto3_session.client("s3")
# s3_resource = boto3_session.resource("s3")
# bucket = s3_resource.Bucket(bucket_name)

# s3_client



def compare_checksums(checksums_a, checksums_b):
    new_objects = {k: v for k, v in checksums_b.items() if k not in checksums_a}
    deleted_objects = {k: v for k, v in checksums_a.items() if k not in checksums_b}
    changed_objects = {k: (checksums_a[k], v) for k, v in checksums_b.items() if k in checksums_a and checksums_a[k] != v}
    return new_objects, deleted_objects, changed_objects


def compare_checksums_names(checksums_a, checksums_b):
    new_objects = {k: v for k, v in checksums_b.items() if k not in checksums_a}
    deleted_objects = {k: v for k, v in checksums_a.items() if k not in checksums_b}
    changed_objects = {k: (checksums_a[k], v) for k, v in checksums_b.items() if k in checksums_a and checksums_a[k] != v}
    return list(new_objects.keys()), list(deleted_objects.keys()), list(changed_objects.keys())

def ensure_query_params_are_passed(query_params, required_names):
    _qp_existence_map = { qp:False for qp in required_names }
    for real_qp_name in query_params.keys():
        _qp_existence_map[real_qp_name] = True
    _all_params_valid = all(_qp_existence_map.values())
    
    if _all_params_valid:
        return _all_params_valid, "Missing query parameters"
    
    missing_params = [k for k,v in _qp_existence_map.items() if v is False]
    return _all_params_valid, f"Missing query parameters {','.join(missing_params)}"


def from_csv_get_kube_name(csv_filepath):
    csv_path = Path(csv_filepath)
    filename = csv_path.stem  # rm '.csv' part  # "kubernetes_pod_metrics"
    if filename.startswith('kubernetes_'):  # Remove 'kubernetes_' prefix
        filename = filename[len('kubernetes_'):]  # "pod_metrics"
    # # Split by underscore and convert to camelCase
    # parts = filename.split('_')
    # camel_case = parts[0].lower() + ''.join(word.capitalize() for word in parts[1:])
    if csv_path.parent.name == 'crds':
        filename = f"crds/{filename}"
    return filename