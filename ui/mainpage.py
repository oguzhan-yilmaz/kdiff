import streamlit as st
from config import boto3_session
from storage import *
from pathlib import Path
import json



st.title("Kdiff UI")
st.header("Connecting to S3 with st.connection")

# print(dir(bucket))
# print('-'*20)
# print(dir(bucket.Tagging))
# print(bucket.bucket_arn, bucket.bucket_region, bucket.creation_date)
# print(bucket.get_available_subresources())


def main():

    all_files = get_all_objects(bucket_name)
    files = filter_files_by_name(bucket_name, 'kdiff-snapshot.metadata.json')

    # for file in metadata_files:
    #     print(f"found {file['Key']}")
        
    s3_snapshot_dirs = get_kdiff_snapshot_metadata_files(bucket_name)
    for mf in s3_snapshot_dirs:
        # print(bucket_name, mf)
        print(mf)


if __name__ == '__main__':
    main()

# for a in bucket.objects.all():
#     print(a)


# with open('filename', 'wb') as data:
#     bucket.download_fileobj('mykey', data)
