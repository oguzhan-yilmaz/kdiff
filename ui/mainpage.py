import streamlit as st
from config import boto3_session
from storage import *
import json



st.title("Kdiff UI")
st.header("Connecting to S3 with st.connection")

# print(dir(bucket))
# print('-'*20)
# print(dir(bucket.Tagging))
# print(bucket.bucket_arn, bucket.bucket_region, bucket.creation_date)
# print(bucket.get_available_subresources())


all_files = get_all_objects(bucket_name)
for file in all_files:
    print(file)
    # print(file['Key'])



# Usage
files = filter_files_by_name(bucket_name, 'kdiff-snapshot-2025-11-02--11-22.tar')

for file in files:
    print(f"found {file['Key']}")


# for a in bucket.objects.all():
#     print(a)


# with open('filename', 'wb') as data:
#     bucket.download_fileobj('mykey', data)
