#!/bin/bash

# Default output directory with timestamp
DEBUG=${DEBUG:-false}

# SQL_LIMIT_STR is expected to be a string like "LIMIT 1000"
SQL_LIMIT_STR=${SQL_LIMIT_STR:-""}

# ======= Command Line Arguments =======
# Add current directory to PATH
export PATH="$PATH:$(pwd)"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --out-dir)
            OUT_DIR="$2"
            shift 2
            ;;
        --debug)
            DEBUG=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--out-dir DIRECTORY] [--debug]"
            exit 1
            ;;
    esac
done

# ======= Logging Functions =======
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

log_debug "Script started with arguments: OUT_DIR=$OUT_DIR, DEBUG=$DEBUG, SQL_LIMIT_STR=$SQL_LIMIT_STR"

# Default output directory with timestamp if not set
OUT_DIR=${OUT_DIR:-"k8s-data-csv-$(date +%Y-%m-%d-%H%M)"}

# Prepend data/ to OUT_DIR
OUT_DIR="data/$OUT_DIR"

# Create output directory if it doesn't exist
log_debug "Creating output directory: $OUT_DIR"
mkdir -p "$OUT_DIR"

log_info "Output directory: $OUT_DIR"
# Get current context and cluster info
log_info "Getting current Kubernetes context and cluster info"
current_context=$(kubectl config current-context)
log_info "Current context: $current_context"

cluster_info=$(kubectl cluster-info)
log_info "Cluster info:"
log_info "$cluster_info"

# ======= Query Tables =======

log_debug "Querying kubernetes tables with limit: $SQL_LIMIT_STR"
tables_sql="SELECT table_name FROM information_schema.tables WHERE table_schema='kubernetes' $SQL_LIMIT_STR"
log_debug "Tables SQL query: $tables_sql"
# Add retries and delay to ensure steampipe service is ready
k8s_tables_max_retries=5
k8s_tables_retry_count=0
while [ $k8s_tables_retry_count -lt $k8s_tables_max_retries ]; do
    if tables=$(steampipe query --header=false --output=csv "$tables_sql" 2>/dev/null); then
        break
    fi
    log_warning "Failed to query tables, retrying in 5 seconds... (Attempt $((k8s_tables_retry_count+1))/$k8s_tables_max_retries)"
    sleep 5
    k8s_tables_retry_count=$((k8s_tables_retry_count+1))
done

if [ $k8s_tables_retry_count -eq $k8s_tables_max_retries ]; then
    log_error "Failed to query tables after $k8s_tables_max_retries attempts"
    exit 1
fi

# Check if tables list is empty
if [ -z "$tables" ]; then
    log_error "No tables found to process. Exiting..."
    rm -rf "$OUT_DIR"
    exit 1
fi

log_debug "Found tables: $tables"


# Process each table
for table in $tables; do
    out_file="${OUT_DIR}/${table}.csv"
    sql_query="SELECT * FROM kubernetes.$table"
    log_debug "Processing table: $table"
    log_debug "Output file: $out_file"
    log_debug "SQL query: $sql_query"
    log_info "Processing table: $table -- $sql_query"

    if [ -z "$sql_query" ]; then
        log_warning "Empty SQL query for table $table, skipping..."
        continue
    fi

    if ! steampipe query --output csv "$sql_query" > "$out_file" 2>/dev/null; then
        log_warning "Failed to query table $table, skipping..."
        continue
    fi
    log_debug ">> Completed processing table: $table"
done




# CRD_LIMIT_STR="LIMIT 5"
crd_sql="SELECT CONCAT('kubernetes_', spec->'names'->>'singular', '_', REPLACE(spec->>'group', '.', '_')) FROM kubernetes.kubernetes_custom_resource_definition $SQL_LIMIT_STR;"
crd_names=$(steampipe query --header=false --output=csv "$crd_sql")
CRD_OUT_DIR="$OUT_DIR/crds"
mkdir -p "$CRD_OUT_DIR"

log_debug "Found crd_names: $crd_names"
for crd_name in $crd_names; do
    # Replace dots and dashes with underscores in CRD name
    crd_sql_query="SELECT * FROM $crd_name"
    log_info "Processing CRD: $crd_name -- $crd_sql_query"
    # log_debug "Processing CRD: $crd_name -- $crd_sql_query"
    if ! steampipe query --output csv "$crd_sql_query" > "$CRD_OUT_DIR/${crd_name}.csv" 2>/dev/null; then
        log_warning "Failed to query CRD $crd_name, skipping..."
        continue
    fi
    log_debug "Completed processing CRD: $crd_name"
done


# Generate checksums for all CSV files
(
    echo "Generating checksums for all CSV files in ${OUT_DIR}"
    cd "${OUT_DIR}"
    find . -name "*.csv" -type f -exec sha256sum {} \; > checksums.txt
)



# ------- Create .metadata.json file -------
# Create .metadata.json file in the OUT_DIR with metadata about the snapshot
metadata_file="${OUT_DIR}/.metadata.json"

# Create metadata file with CLI versions, cluster info, and snapshot details

cat << EOF | tee "$metadata_file"
{
  "cliVersions": {
    "kubectl": $(kubectl version --client -o json 2>/dev/null | jq '.clientVersion.gitVersion' || echo '""'),
    "aws": "$(aws --version 2>&1)",
    "qsv": "$(qsv --version 2>&1)", 
    "jq": "$(jq --version 2>&1)",
    "steampipe": "$(steampipe --version 2>&1)"
  },
  "snapshotInfo": {
    "timestamp": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
    "hostname": "${HOSTNAME:-}",
    "sql_limit_str": "${SQL_LIMIT_STR:-}",
    "s3_bucket_name": "${S3_BUCKET_NAME:-}",
    "s3_upload_prefix": "${S3_UPLOAD_PREFIX:-}",
    "aws_endpoint_url_s3": "${AWS_ENDPOINT_URL_S3:-AWS S3}"
  }
}
EOF

echo "Created metadata file: $metadata_file"


    

log_debug "Script completed successfully"


