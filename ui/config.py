import boto3
import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


# Read S3 configuration from environment variables
aws_endpoint_url = os.environ.get("AWS_ENDPOINT_URL_S3")
aws_access_key_id = os.environ.get("AWS_ACCESS_KEY_ID")
aws_secret_access_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
aws_default_region = os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION") 
bucket_name = os.environ.get("BUCKET_NAME")
local_dir_for_s3_sync = os.environ.get("KDIFF_SNAPSHOTS_DIR")
active_diff_dir = os.environ.get("KDIFF_ACTIVE_DIFF_DIR")

s3_client_args = {
    # "endpoint_url": aws_endpoint_url,
    "aws_access_key_id": aws_access_key_id,
    "aws_secret_access_key": aws_secret_access_key,
    "region_name": aws_default_region,
}

# aws_access_key_id=None, aws_secret_access_key=None, aws_session_token=None, region_name=None, botocore_session=None, profile_name=None, aws_account_id=None
boto3_session = boto3.session.Session(**s3_client_args)
