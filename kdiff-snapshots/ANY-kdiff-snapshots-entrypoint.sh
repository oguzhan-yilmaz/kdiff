#!/bin/bash

# ======= CONFIGURABLE RETRY MECHANISM =======
# Environment variables for retry configuration
MAX_RETRIES=${MAX_RETRIES:-3}
RETRY_DELAY=${RETRY_DELAY:-5}
RETRY_BACKOFF_MULTIPLIER=${RETRY_BACKOFF_MULTIPLIER:-2}
export STEAMPIPE_PLUGIN_NAME=${STEAMPIPE_PLUGIN_NAME}
# Debug mode
DEBUG=${DEBUG:-false}

# SQL_LIMIT_STR is expected to be a string like "LIMIT 1000"
SQL_LIMIT_STR=${SQL_LIMIT_STR:-""}

# ======= LOGGING FUNCTIONS =======
log_debug() {
    if [[ "$DEBUG" == "true" ]]; then
        echo "[DEBUG] $1"
    fi
}

log_info() {
    echo "[INFO] $1"
}

log_warning() {
    echo "[WARNING] $1"
}

log_error() {
    echo "[ERROR] $1"
}

log_success() {
    echo "[SUCCESS] $1"
}

required_vars=("STEAMPIPE_PLUGIN_NAME" "MAX_RETRIES" "RETRY_DELAY" "RETRY_BACKOFF_MULTIPLIER" "DEBUG")

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: Required environment variable $var is not set. Aborting..." >&2
        exit 1
    fi
done

# ======= RETRY FUNCTION =======
retry_with_backoff() {
    local cmd="$1"
    local description="$2"
    local retry_count=0
    local current_delay=$RETRY_DELAY
    
    log_info "Starting: $description"
    log_debug "Retry configuration: MAX_RETRIES=$MAX_RETRIES, RETRY_DELAY=$RETRY_DELAY, BACKOFF_MULTIPLIER=$RETRY_BACKOFF_MULTIPLIER"
    
    while [ $retry_count -lt $MAX_RETRIES ]; do
        log_debug "Attempt $((retry_count + 1))/$MAX_RETRIES"
        
        if eval "$cmd"; then
            log_success "$description completed successfully"
            return 0
        else
            retry_count=$((retry_count + 1))
            
            if [ $retry_count -lt $MAX_RETRIES ]; then
                log_warning "$description failed (attempt $retry_count/$MAX_RETRIES). Retrying in ${current_delay} seconds..."
                sleep $current_delay
                current_delay=$((current_delay * RETRY_BACKOFF_MULTIPLIER))
            else
                log_error "$description failed after $MAX_RETRIES attempts"
                return 1
            fi
        fi
    done
}

# ======= INITIAL CHECKS =======
log_info "Starting kdiff-snapshots-entrypoint.sh with retry mechanism"

if [ -z "$S3_BUCKET_NAME" ]; then
    log_error "S3_BUCKET_NAME environment variable is not set. Aborting."
    exit 1
fi

if [ -z "$S3_UPLOAD_PREFIX" ]; then
    log_error "S3_UPLOAD_PREFIX environment variable is not set. Aborting."
    exit 1
fi

# Check if AWS_DEFAULT_REGION is not set, try to detect from bucket
if [ -z "$AWS_DEFAULT_REGION" ]; then
    log_info "AWS_DEFAULT_REGION not set, attempting to detect from bucket location..."
    
    # Get bucket location using AWS CLI with retry
    retry_with_backoff \
        "aws s3api get-bucket-location --bucket \"$S3_BUCKET_NAME\" 2>/dev/null | jq -r '.LocationConstraint // \"us-east-1\"'" \
        "Detect bucket region"
    
    if [ $? -eq 0 ]; then
        # Parse the JSON response
        export AWS_REGION=$(aws s3api get-bucket-location --bucket "$S3_BUCKET_NAME" 2>/dev/null | jq -r '.LocationConstraint // "us-east-1"')
        export AWS_DEFAULT_REGION="$AWS_REGION"
        log_info "Detected bucket region: $AWS_DEFAULT_REGION"
    else
        log_warning "Could not detect bucket region. AWS credentials may be invalid or bucket may not exist."
        log_warning "Please set AWS_DEFAULT_REGION manually if needed."
    fi
fi

# ======= INSTALL PLUGINS =======
if [ -n "$INSTALL_STEAMPIPE_PLUGINS" ]; then
    log_info "Installing Plugins: $INSTALL_STEAMPIPE_PLUGINS"
    for mod in $INSTALL_STEAMPIPE_PLUGINS; do
        log_info "Installing Plugin: $mod"
        retry_with_backoff \
            "steampipe plugin install \"$mod\" > /dev/null" \
            "Install steampipe plugin: $mod"
    done
fi

log_info "Updating Plugins..."
retry_with_backoff \
    "steampipe plugin update --all" \
    "Update all steampipe plugins"

log_info "Steampipe Plugins:"
steampipe plugin list

# ======= INIT DB =======
# run the initdb.sh in a sub-shell to not block the steampipe service start
if [ -f "init-db.sh" ]; then
    log_info "Running init-db.sh script..."
    (bash init-db.sh) &
fi

# ======= START STEAMPIPE SERVICE =======
log_info "Starting steampipe service..."
retry_with_backoff \
    "bash start-and-wait-steampipe-service.sh" \
    "Start and wait for steampipe service"

log_info "------------*------------*------------"

# ======= BACKUP KUBERNETES STATE =======

base_epoch=$(date -u +%s)

if date -u -d "@$base_epoch" +"%Y-%m-%dT%H:%M:%SZ" >/dev/null 2>&1; then
  # GNU date
  timestamp_iso=$(date -u -d "@$base_epoch" +"%Y-%m-%dT%H:%M:%SZ")
  timestamp_dir=$(date -u -d "@$base_epoch" +"%Y-%m-%d--%H-%M")
else
  # BSD date (macOS)
  timestamp_iso=$(date -u -r "$base_epoch" +"%Y-%m-%dT%H:%M:%SZ")
  timestamp_dir=$(date -u -r "$base_epoch" +"%Y-%m-%d--%H-%M")
fi

log_debug "timestamp_iso=$timestamp_iso"
log_debug "timestamp_dir=$timestamp_dir"


# timestamp=$(date +"%Y-%m-%d--%H-%M")
export SNP_FOLDER_NAME="kdiff-snp-${timestamp_dir}"
export DIR_NAME="${STEAMPIPE_PLUGIN_NAME}/${SNP_FOLDER_NAME}"
export DIR_TAR_NAME="$DIR_NAME.tar"

log_info "Running ANY-csv-script.sh to export Kubernetes resources to CSV files in data/$DIR_NAME..."
retry_with_backoff \
    "bash ANY-csv-script.sh --out-dir \"$DIR_NAME\" \$([ \"$DEBUG\" = \"true\" ] && echo \"--debug\")" \
    "Export Kubernetes resources to CSV"

ls -al "data/$DIR_NAME"
log_info "------------*------------*------------"




metadata_file="data/${DIR_NAME}/kdiff-snapshot.metadata.json"
extra_metadata=$(cat <<EOF
{
  "DIR_NAME": "${DIR_NAME}",
  "S3_UPLOAD_PREFIX": "${S3_UPLOAD_PREFIX}",
  "timestamp_iso": "$timestamp_iso",
  "timestamp_dir": "$timestamp_dir",
  "added_from": "entrypoint bash script"
}
EOF
)
# jq . "$extra_metadata" >/dev/null && echo "extra_metadata valid JSON" || echo "extra_metadata invalid JSON"
new_metadata_json=$(jq --argjson extra "$extra_metadata" '.snapshotInfo += $extra' "$metadata_file")
# jq . "$new_metadata_json" >/dev/null && echo "new_metadata_json valid JSON" || echo "new_metadata_json invalid JSON"

echo "$new_metadata_json" > "$metadata_file"
log_info "Updated snapshotInfo on metadata file..."

mkdir -p "tars/${STEAMPIPE_PLUGIN_NAME}"
# tar the snapshot
log_info "Creating tar archive..."
log_debug "Running command: tar -cf \"tars/$DIR_TAR_NAME\" -C \"data/$STEAMPIPE_PLUGIN_NAME\" \"$SNP_FOLDER_NAME\" "
retry_with_backoff \
    "tar -cf \"tars/$DIR_TAR_NAME\" -C \"data/$STEAMPIPE_PLUGIN_NAME\" \"$SNP_FOLDER_NAME\"" \
    "Create tar archive tars/$DIR_TAR_NAME"
tar: kdiff-snp-2025-11-12--16-21: Cannot stat: No such file or directory
tar: Error exit delayed from previous errors.
log_success "Successfully created tar archive at tars/$DIR_TAR_NAME"
ls -alh "tars/$DIR_TAR_NAME"
log_info "Archive contents:"
tar -tvf "tars/$DIR_TAR_NAME"

# ======= S3 UPLOAD =======
log_info "------------*------------*------------"

if [ "$DEBUG" = "true" ]; then
    log_debug "Checking AWS credentials..."
    aws sts get-caller-identity
    log_debug "AWS Region configuration:"
    log_debug "AWS_REGION=${AWS_REGION:-not set}"
    log_debug "AWS_DEFAULT_REGION=${AWS_DEFAULT_REGION:-not set}"
    log_debug "Listing contents of S3 bucket ${S3_BUCKET_NAME}..."
    aws s3 ls s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX}/${STEAMPIPE_PLUGIN_NAME}
    ls -alh
fi

log_info "Uploading tar archive to s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/tars/${DIR_TAR_NAME}"
retry_with_backoff \
    "aws s3 cp \"tars/$DIR_TAR_NAME\" s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/tars/${DIR_TAR_NAME}" \
    "Upload tar archive to S3"

log_info "Uploading snapshot objects to s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/${DIR_NAME}"
retry_with_backoff \
    "aws s3 cp \"data/$DIR_NAME\" s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/${DIR_NAME} --recursive" \
    "Upload snapshot objects to S3"


log_info "------------*------------*------------"

log_info "Listing s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX}/${STEAMPIPE_PLUGIN_NAME}"
echo "---"
aws s3 ls "s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX}/${STEAMPIPE_PLUGIN_NAME}/"

log_info "Download with command:"
log_info "    aws s3 cp s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/tars/${STEAMPIPE_PLUGIN_NAME}${DIR_TAR_NAME} ."
log_info "    aws s3 cp s3://${S3_BUCKET_NAME}/${S3_UPLOAD_PREFIX%/}/${DIR_NAME} ${DIR_NAME} --recursive"

# ======= CLEANUP =======
log_info "Cleaning up temporary files..."
# rm -rf "/data/$DIR_NAME"
rm -f "tars/$DIR_TAR_NAME"

# ======= DEBUG MODE =======
if [ "$DEBUG" = "true" ]; then
    log_info "DEBUG mode enabled - sleeping indefinitely..."
    sleep infinity
fi

log_success "kdiff-snapshots-entrypoint.sh completed successfully"
