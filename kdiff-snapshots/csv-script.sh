#!/bin/bash

# Default output directory with timestamp
OUT_DIR="k8s-data-csv-$(date +%Y-%m-%d-%H%M)"
DEBUG=false

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

log_debug "Script started with arguments: OUT_DIR=$OUT_DIR, DEBUG=$DEBUG"

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

LIMIT_STR="LIMIT 3"
log_debug "Querying kubernetes tables with limit: $LIMIT_STR"
tables=$(steampipe query --header=false --output=csv "SELECT table_name FROM information_schema.tables WHERE table_schema = 'kubernetes' $LIMIT_STR")
log_debug "Found tables: $tables"

# Process each table
for table in $tables; do
    out_file="${OUT_DIR}/${table}.csv"
    sql_query="SELECT * FROM kubernetes.$table"
    log_debug "Processing table: $table"
    log_debug "Output file: $out_file"
    log_debug "SQL query: $sql_query"
    log_info "Processing table: $table -- $sql_query"
    echo "$sql_query" \
        | steampipe query --output csv > "$out_file"
    log_debug "Completed processing table: $table"
done

log_debug "Script completed successfully"




CRD_LIMIT_STR="LIMIT 5"
crd_sql="SELECT CONCAT('kubernetes_', spec->'names'->>'singular', '_', REPLACE(spec->>'group', '.', '_')) FROM kubernetes.kubernetes_custom_resource_definition $CRD_LIMIT_STR;"
crd_names=$(steampipe query --header=false --output=csv "$crd_sql")
CRD_OUT_DIR="$OUT_DIR/crds"


log_debug "Found crd_names: $crd_names"
for crd_name in $crd_names; do
    # Replace dots and dashes with underscores in CRD name

    log_info "Processing CRD: $crd_name"
    mkdir -p "$CRD_OUT_DIR"
    crd_sql_query="SELECT * FROM $crd_name"
    log_debug "Processing CRD: $crd_name -- $crd_sql_query"
    echo "$crd_sql_query" \
        | steampipe query --output csv > "$CRD_OUT_DIR/${crd_name}.csv"
    log_debug "Completed processing CRD: $crd_name"
done


# Generate checksums for all CSV files
(
    echo "Generating checksums for all CSV files in ${OUT_DIR}"
    cd "${OUT_DIR}"
    find . -name "*.csv" -type f -exec sha256sum {} \; > checksums.txt
)


log_debug "Script completed successfully"


