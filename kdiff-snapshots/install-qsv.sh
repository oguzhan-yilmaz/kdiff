#!/usr/bin/env bash
#
# install-qsv.sh — Install qsv depending on CPU architecture (amd64 or arm64)
#
# This script installs qsv using the appropriate method for your platform.
# Requires: bash, wget, unzip, sudo, apt
#
# Usage:
#   chmod +x install-qsv.sh
#   ./install-qsv.sh
#

set -euo pipefail
IFS=$'\n\t'

# --- Functions ---------------------------------------------------------------

log() {
    # Simple logging helper
    echo "[INFO] $*"
}

error_exit() {
    echo "[ERROR] $*" >&2
    exit 1
}

install_qsv_amd64() {
    log "Detected amd64 architecture. Installing qsv via APT repository..."

    # Import GPG key and add repository
    wget -qO- https://dathere.github.io/qsv-deb-releases/qsv-deb.gpg \
        | sudo gpg --dearmor -o /usr/share/keyrings/qsv-deb.gpg

    echo "deb [signed-by=/usr/share/keyrings/qsv-deb.gpg] https://dathere.github.io/qsv-deb-releases ./" \
        | sudo tee /etc/apt/sources.list.d/qsv.list > /dev/null

    # Update and install qsv
    sudo apt update -y
    sudo apt install -y qsv

    log "qsv installation complete (amd64)."
}

install_qsv_arm64() {
    log "Detected arm64 architecture. Installing qsv manually..."

    QSV_VER="8.1.1"
    QSV_DOWNLOAD_URL="https://github.com/dathere/qsv/releases/download/${QSV_VER}/qsv-${QSV_VER}-aarch64-unknown-linux-gnu.zip"

    log "Downloading QSV version ${QSV_VER} from ${QSV_DOWNLOAD_URL}"

    wget -q "${QSV_DOWNLOAD_URL}"
    unzip -q "qsv-${QSV_VER}-aarch64-unknown-linux-gnu.zip"
    rm "qsv-${QSV_VER}-aarch64-unknown-linux-gnu.zip"

    log "Listing extracted files:"
    ls -R

    log "qsv installation complete (arm64)."
}

# --- Main --------------------------------------------------------------------

main() {
    ARCH="$(uname -m)"
    log "Detected architecture: ${ARCH}"

    case "${ARCH}" in
        x86_64|amd64)
            install_qsv_amd64
            ;;
        arm64|aarch64)
            install_qsv_arm64
            ;;
        *)
            error_exit "Unsupported architecture: ${ARCH}"
            ;;
    esac
}
ls -R
main "$@"
ls -R