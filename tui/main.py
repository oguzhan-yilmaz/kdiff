from config import ui_config, boto3_session
from storage import *

def main():
    print("Hello from tui!")
    s3_remote_available_plugins = list_folders(bucket_name, snapshots_s3_prefix)
    print(s3_remote_available_plugins)
    

if __name__ == "__main__":
    main()
