#!/bin/bash

DEBUG=${DEBUG:-true}


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

if [ -n "$INSTALL_PLUGINS" ]; then
    echo "Installing Plugins: $INSTALL_PLUGINS"
    for mod in $INSTALL_PLUGINS; do
        echo "Installing Plugin: $mod"
        steampipe plugin install "$mod" > /dev/null
    done
fi

echo "Updating Plugins..."
steampipe plugin update --all

echo "Steampipe Plugins:"
steampipe plugin list

# # ----------- INIT DB -----------

# # run the initdb.sh in a sub-shell to not block the steampipe service start
# (bash init-db.sh) &

# ----------- START STEAMPIPE -----------

echo "Starting Steampipe:"
steampipe service start --foreground

steampipe service status
# ----------- BACKUP KUBERNETES STATE -----------
# snapshot kubernetes state

export DIR_NAME="kdiff-snapshot-$(date +"%Y-%m-%d--%H-%M")"
export DIR_TAR_NAME="$DIR_NAME.tar.gz"

bash csv-script.sh --debug --out-dir "/tmp/$DIR_NAME"


ls -al "/tmp/$DIR_NAME"

# tar the snapshot
tar -czf "/tmp/$DIR_TAR_NAME" "/tmp/$DIR_NAME"



# upload the snapshot to s3


if [ "$DEBUG" = "true" ]; then
    aws sts get-caller-identity
fi

# ----------- S3 UPLOAD -----------
echo "Uploading to s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/${DIR_TAR_NAME}"
aws s3 cp "/tmp/$DIR_TAR_NAME" s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/${DIR_TAR_NAME}
echo "------------*------------*------------"

echo "Listing  s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX}"
echo "---"
aws s3 ls s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX}

echo "Download with command:"
echo "    aws s3 cp s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/${DIR_TAR_NAME} ."


if [ "$DEBUG" = "true" ]; then
    sleep infinity
fi
