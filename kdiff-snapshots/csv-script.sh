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

# ======= Query Tables =======

log_debug "Querying kubernetes tables with limit: ${SQL_LIMIT_STR:-N/A}"
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

log_debug "Found $(echo "$tables" | wc -l) tables"

mkdir "${OUT_DIR}/_table_metadata/"
# Process each table
for table in $tables; do
    out_file="${OUT_DIR}/${table}.csv"
    sql_query="SELECT * FROM kubernetes.$table"
    log_debug "Processing table: $table  -- Output file: $out_file -- SQL query: $sql_query"
    if [ -z "$sql_query" ]; then
        log_warning "Empty SQL query for table $table, skipping..."
        continue
    fi

    if ! steampipe query --output csv "$sql_query" > "$out_file" 2>/dev/null; then
        log_warning "Failed to query table $table, skipping..."
        continue
    fi

    # Get table metadata
    metadata_out_file="${OUT_DIR}/_table_metadata/${table}.metadata.json"
    metadata_sql_query="SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema = 'kubernetes' AND table_name = '$table'"
    log_debug "Fetching metadata for table: $table -- Output file: $metadata_out_file"
    if ! steampipe query --output json "$metadata_sql_query" > "$metadata_out_file" 2>/dev/null; then
        log_warning "Failed to query metadata for table $table, skipping..."
    fi
    log_debug ">> Completed processing table: $table to $metadata_out_file"
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

    # Get CRD table metadata
    metadata_out_file="${CRD_OUT_DIR}/${crd_name}.metadata.json"
    metadata_sql_query="SELECT column_name, data_type, is_nullable, column_default FROM information_schema.columns WHERE table_schema = 'kubernetes' AND table_name = '$crd_name'"
    log_debug "Fetching metadata for CRD table: $crd_name -- Output file: $metadata_out_file"
    if ! steampipe query --output json "$metadata_sql_query" > "$metadata_out_file" 2>/dev/null; then
        log_warning "Failed to query metadata for CRD table $crd_name, skipping..."
    fi

    log_debug "Completed processing CRD: $crd_name"
done


# Generate checksums for all CSV files
(
    echo "Generating checksums for all CSV files in ${OUT_DIR}"
    cd "${OUT_DIR}"
    find . -name "*.csv" -o -name "*.metadata.json" -type f -exec sha256sum {} + > checksums.txt
)

checksums_json=$(
  cd "${OUT_DIR}" || exit 1

  # Compute sha256sums for all CSV and metadata files
  # Format: {"filename":"checksum"}
  find . -type f \( -name "*.csv" -o -name "*.metadata.json" \) \
    -exec sha256sum {} + |
    awk '{print "{\"" substr($2,3) "\":\"" $1 "\"}"}' |  # remove "./" prefix from filename
    jq -s 'add'  # merge all small JSON objects into one
)

# ------- Create .metadata.json file -------
# Create .metadata.json file in the OUT_DIR with metadata about the snapshot
metadata_file="${OUT_DIR}/kdiff-snapshot.metadata.json"
log_info "metadata_file=$metadata_file"

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
    "output_directory": "${OUT_DIR}",
    "sql_limit_str": "${SQL_LIMIT_STR:-}",
    "s3_bucket_name": "${S3_BUCKET_NAME:-}",
    "s3_upload_prefix": "${S3_UPLOAD_PREFIX:-}",
    "aws_endpoint_url_s3": "${AWS_ENDPOINT_URL_S3:-AWS S3}"
  }
}
EOF

kdiff_metadata_json=$(jq --argjson checksums "${checksums_json}" '. + {checksums: $checksums}'  "$metadata_file")
log_debug "kdiff_metadata_json==$kdiff_metadata_json"
echo "$kdiff_metadata_json" > "$metadata_file"

log_info "Created metadata file: $metadata_file"
    
log_debug "csv-script.sh completed successfully"


