#!/bin/bash

DEBUG=${DEBUG:-false}

# SQL_LIMIT_STR is expected to be a string like "LIMIT 1000"
SQL_LIMIT_STR=${SQL_LIMIT_STR:-""}

# ------ INITIAL CHECKS -----------

if [ -z "$S3_BUCKET_NAME" ]; then
    echo "Error: S3_BUCKET_NAME environment variable is not set. Aborting."
    exit 1
fi

if [ -z "$S3_UPLOAD_PREFIX" ]; then
    echo "Error: S3_UPLOAD_PREFIX environment variable is not set. Aborting."
    exit 1
fi

# Check if AWS_DEFAULT_REGION is not set, try to detect from bucket
if [ -z "$AWS_DEFAULT_REGION" ]; then
    echo "AWS_DEFAULT_REGION not set, attempting to detect from bucket location..."
    
    # Get bucket location using AWS CLI
    BUCKET_LOCATION=$(aws s3api get-bucket-location --bucket "$S3_BUCKET_NAME" 2>/dev/null)
    
    if [ $? -eq 0 ]; then
        # Parse the JSON response
        AWS_REGION=$(echo "$BUCKET_LOCATION" | jq -r '.LocationConstraint // "us-east-1"')
        
        # Special case: null means us-east-1
        if [ "$AWS_REGION" = "null" ]; then
            AWS_REGION="us-east-1"
        fi
        
        export AWS_DEFAULT_REGION="$AWS_REGION"
        echo "Detected bucket region: $AWS_DEFAULT_REGION"
    else
        echo "Warning: Could not detect bucket region. AWS credentials may be invalid or bucket may not exist."
        echo "Please set AWS_DEFAULT_REGION manually if needed."
    fi
fi


# ----------- INSTALL PLUGINS -----------

if [ -n "$INSTALL_STEAMPIPE_PLUGINS" ]; then
    echo "Installing Plugins: $INSTALL_STEAMPIPE_PLUGINS"
    for mod in $INSTALL_STEAMPIPE_PLUGINS; do
        echo "Installing Plugin: $mod"
        steampipe plugin install "$mod" > /dev/null
    done
fi

echo "Updating Plugins..."
steampipe plugin update --all

echo "Steampipe Plugins:"
steampipe plugin list

# ----------- INIT DB -----------

# run the initdb.sh in a sub-shell to not block the steampipe service start
if [ -f "init-db.sh" ]; then
    echo "Running init-db.sh script..."
    (bash init-db.sh) &
fi

# ----------- START STEAMPIPE SERVICE -----------

bash start-and-wait-steampipe-service.sh

# ----------- BACKUP KUBERNETES STATE -----------
# snapshot kubernetes state

export DIR_NAME="kdiff-snapshot-$(date +"%Y-%m-%d--%H-%M")"
export DIR_TAR_NAME="$DIR_NAME.tar.gz"

echo "Running csv-script.sh to export Kubernetes resources to CSV files in data/$DIR_NAME..."
if ! bash csv-script.sh --out-dir "$DIR_NAME" $([ "$DEBUG" = "true" ] && echo "--debug"); then
    echo "Error: csv-script.sh failed. Aborting."
    exit 1
fi

ls -al "$DIR_NAME"
mkdir -p tars/
# tar the snapshot
echo "Creating tar archive..."
echo "Running command: tar -czf \"tars/$DIR_TAR_NAME\" -C \"data/$DIR_NAME\" ."
if ! tar -czf "tars/$DIR_TAR_NAME" -C "data/$DIR_NAME" .; then
    echo "Error: Failed to create $DIR_TAR_NAME tar archive. Aborting."
    echo "tar exit code: $?"
    exit 1
fi
echo "Successfully created tar archive at tars/$DIR_TAR_NAME"
echo "Archive contents:"
tar -tvf "tars/$DIR_TAR_NAME"

# upload the snapshot to s3

if [ "$DEBUG" = "true" ]; then
    echo "Checking AWS credentials..."
    aws sts get-caller-identity
    echo "Listing contents of S3 bucket ${S3_BUCKET_NAME}..."
    aws s3 ls s3://${S3_BUCKET_NAME}
fi

# ----------- S3 UPLOAD -----------
echo "Uploading to s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/${DIR_TAR_NAME}"
if ! aws s3 cp "/tmp/$DIR_TAR_NAME" s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/${DIR_TAR_NAME}; then
    echo "Error: Failed to upload $DIR_TAR_NAME to s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/${DIR_TAR_NAME}. Aborting."
    exit 1
fi

echo "------------*------------*------------"

echo "Listing s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX}"
echo "---"
aws s3 ls s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX}

echo "Download with command:"
echo "    aws s3 cp s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/${DIR_TAR_NAME} ."

# Cleanup temporary files
echo "Cleaning up temporary files..."
rm -rf "/tmp/$DIR_NAME"
rm -f "/tmp/$DIR_TAR_NAME"



if [ "$DEBUG" = "true" ]; then
    sleep infinity
fi
