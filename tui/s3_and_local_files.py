import subprocess
import sys

def run_aws_cli_sync(bucket_name, s3_folder, local_folder, include_pattern='*.csv', 
                     delete=False, dry_run=False):
    """
    Run AWS CLI s3 sync command from Python.
    
    Args:
        bucket_name (str): S3 bucket name
        s3_folder (str): S3 folder path
        local_folder (str): Local directory path
        include_pattern (str): File pattern to include (default: '*.csv')
        delete (bool): Delete local files not in S3
        dry_run (bool): Show what would be synced without actually syncing
    """
    # Build the command
    cmd = [
        'aws', 's3', 'sync',
        f's3://{bucket_name}/{s3_folder}',
        local_folder
    ]
    
    # Add filters for CSV files only
    if include_pattern:
        cmd.extend(['--exclude', "'*'"])
        cmd.extend(['--include', f"'{include_pattern}'"])
    
    # Add optional flags
    if delete:
        cmd.append('--delete')
    
    if dry_run:
        cmd.append('--dryrun')
    
    # print(f"🔄 Running: {' '.join(cmd)}\n")
    
    try:
        # Method 1: Simple run with output to console
        result = subprocess.run(cmd, check=True, text=True, 
                              capture_output=True)
        
        # Print output
        # if result.stdout:
        #     print(result.stdout)
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        print("✅ Sync completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running AWS CLI command:")
        print(f"   Exit code: {e.returncode}")
        # if e.stdout:
        #     print(f"   Output: {e.stdout}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return False
    except FileNotFoundError:
        print("❌ AWS CLI not found. Please install it:")
        print("   https://aws.amazon.com/cli/")
        return False
    
    
def run_any_bash_command(command):
    """
    Run any bash command from Python.
    
    Args:
        command (str): The bash command to run
    """
    # print(f"🔄 Running: {command}\n")
    
    try:
        # Run command using shell
        # result = subprocess.run(
        #     ["bash", "-c", command],    # force bash!
        #     # command,
        #     shell=True,
        #     check=True,
        #     text=True,
        #     capture_output=True
        # )
        
        result = subprocess.run(
            ["bash", "-c", command],
            check=True,
            text=True,
            stdout=subprocess.PIPE,     # capture only if you *need* it
            stderr=sys.stderr           # stream stderr live
        )

        # if result.stdout:
        #     print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        return result.stdout
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        if e.stderr:
            print(f"   Error: {e.stderr}")
        return None


def check_aws_cli_installed():
    """Check if AWS CLI is installed and configured."""
    try:
        result = subprocess.run(['aws', '--version'], 
                              capture_output=True, text=True)
        print(f"✅ AWS CLI installed: {result.stdout.strip()}")
        
        # Check if credentials are configured
        result = subprocess.run(['aws', 'sts', 'get-caller-identity'],
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ AWS credentials configured")
            return True
        else:
            print("⚠️  AWS credentials not configured")
            return False
    except FileNotFoundError:
        print("❌ AWS CLI not installed")
        return False


if __name__ == "__main__":
    # Configuration
    pass


