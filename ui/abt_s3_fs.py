import streamlit as st
from st_files_connection import FilesConnection

st.title("Kdiff UI")
st.header("Connecting to S3 with st.connection")

# Initialize connection to S3 using configuration from .streamlit/secrets.toml
conn = st.connection("s3", type=FilesConnection)

bucket_name = "test-bucket"
st.subheader(f"Listing files in bucket: `{bucket_name}`")

# The listdir() method is a convenient way to get a list of files.
conn
conn.fs
filesystem = conn.fs
filesystem