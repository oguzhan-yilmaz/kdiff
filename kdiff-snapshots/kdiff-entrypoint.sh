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

# ----------- CHECK STEAMPIPE SERVICE -----------

echo "Starting Steampipe Service..."
steampipe service start

sleep 4

echo "Steampipe Service Status:"
steampipe service status
echo "------------*------------*------------"

# ----------- BACKUP KUBERNETES STATE -----------
# snapshot kubernetes state

export DIR_NAME="kdiff-snapshot-$(date +"%Y-%m-%d--%H-%M")"
export DIR_TAR_NAME="$DIR_NAME.tar.gz"

echo "Running csv-script.sh to export Kubernetes resources to CSV files in /tmp/$DIR_NAME..."
if ! bash csv-script.sh --out-dir "/tmp/$DIR_NAME" --sql-limit-str "$SQL_LIMIT_STR" $([ "$DEBUG" = "true" ] && echo "--debug"); then
    echo "Error: csv-script.sh failed. Aborting."
    exit 1
fi

ls -al "/tmp/$DIR_NAME"

# tar the snapshot
echo "Creating tar archive..."
if ! tar -czf "/tmp/$DIR_TAR_NAME" -C "/tmp" "$DIR_NAME"; then
    echo "Error: Failed to create $DIR_TAR_NAME tar archive. Aborting."
    exit 1
fi

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
