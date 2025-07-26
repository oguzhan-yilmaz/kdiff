# kdiff

[![Artifact Hub](https://img.shields.io/endpoint?url=https://artifacthub.io/badge/repository/kdiff-snapshots)](https://artifacthub.io/packages/search?repo=kdiff-snapshots)

A comprehensive Kubernetes data management and comparison toolkit that provides both CLI tools for local folder comparison and Helm-based solutions for generating complete cluster snapshots.

## Overview

kdiff consists of two main components:

1. **kdiff-cli**: A Python-based command-line tool for comparing folders and files
2. **kdiff-snapshots**: A Kubernetes-native Helm chart that deploys Steampipe to generate comprehensive CSV snapshots of your cluster data

## Quick Start

### kdiff-snapshots (Helm Chart)

The primary component for Kubernetes cluster data export:

```bash
# Add the Helm repository
helm repo add kdiff-snapshots https://oguzhan-yilmaz.github.io/kdiff/
helm repo update kdiff-snapshots

# Get the default values and change them 
helm show values kdiff-snapshots > kdiff-snapshots.values.yaml

helm upgrade --install kdiff-snapshots \
    -f kdiff-snapshots.values.yaml \
    kdiff-snapshots/kdiff-snapshots
```

### Using ArgoCD

```bash
# Apply the ArgoCD application for GitOps deployment
kubectl apply -f kdiff-snapshots.argocd-app.yaml
```

## Components

### kdiff-snapshots

A Kubernetes-native solution for generating comprehensive CSV snapshots of your Kubernetes cluster data using Steampipe.

**Features:**
- Complete cluster snapshot generation
- CRD support and automatic detection
- Multi-cloud plugin support (AWS, GCP, Azure)
- Read-only RBAC permissions
- ArgoCD-ready deployment
- Configurable Steampipe plugins

**Documentation:** [kdiff-snapshots/README.md](kdiff-snapshots/README.md)

### kdiff-cli

A Python CLI tool for comparing folders and files (currently in development).

**Features:**
- Folder comparison with hash-based content verification
- File difference detection
- Progress reporting
- Configurable output formats

**Documentation:** [kdiff-cli/README.md](kdiff-cli/README.md)


## Getting Started

### Installation Steps

1. **Add the Helm repository:**
   ```bash
   helm repo add kdiff-snapshots https://oguzhan-yilmaz.github.io/kdiff/
   helm repo update kdiff-snapshots
   ```

2. **Install the chart:**
   ```bash
   helm upgrade --install kdiff-snapshots kdiff-snapshots/kdiff-snapshots
   ```
