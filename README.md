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

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   kdiff-cli     │    │ kdiff-snapshots  │    │   Kubernetes    │
│   (Local)       │    │   (Helm Chart)   │    │    Cluster      │
│                 │    │                  │    │                 │
│ • Folder diff   │    │ • Steampipe      │    │ • Pods          │
│ • File compare  │    │ • CSV Export     │    │ • Services      │
│ • Hash verify   │    │ • Multi-cloud    │    │ • CRDs          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Use Cases

### Cluster Auditing
Generate complete snapshots of your Kubernetes cluster for compliance, auditing, and backup purposes.

### Multi-Environment Comparison
Compare cluster states across different environments (dev, staging, production).

### Data Export
Export Kubernetes data to CSV format for analysis in external tools.

## Getting Started

### Installation Steps

1. **Add the Helm repository:**
   ```bash
   helm repo add kdiff-snapshots https://oguzhan-yilmaz.github.io/kdiff/
   helm repo update
   ```

2. **Install the chart:**
   ```bash
   helm install kdiff-snapshots kdiff-snapshots/kdiff-snapshots
   ```

3. **Verify installation:**
   ```bash
   kubectl get pods -l app.kubernetes.io/name=kdiff-snapshots
   ```

4. **Access the service:**
   ```bash
   kubectl port-forward deployment/kdiff-snapshots 9193:9193
   ```


## Configuration Examples

### Multi-Cloud Setup

```yaml
# values.yaml
steampipe:
  envVars:
    INSTALL_STEAMPIPE_PLUGINS: "kubernetes aws gcp azure"
    AWS_PROFILE: "production"
    GCP_PROJECT: "my-gcp-project"
  
  secretEnvVars:
    AWS_ACCESS_KEY_ID: "your-aws-key"
    AWS_SECRET_ACCESS_KEY: "your-aws-secret"
```


## Usage Examples

### Generate Cluster Snapshot

```bash
# The container automatically generates snapshots on startup
# Check the generated files
kubectl exec -it deployment/kdiff-snapshots -- ls -la /tmp/kdiff-snapshots/
```

### Query Steampipe API

```bash
# Query Kubernetes pods
curl http://localhost:9193/v1/query \
  -d '{"sql": "SELECT name, namespace, status FROM kubernetes.kubernetes_pod LIMIT 5"}'
```

### Manual Snapshot Generation

```bash
# Execute snapshot script manually
kubectl exec -it deployment/kdiff-snapshots \
  -- bash csv-script.sh --debug --out-dir /tmp/manual-snapshots
```


## Support

- **Issues**: [GitHub Issues](https://github.com/oguzhan-yilmaz/kdiff/issues)
- **Documentation**: [kdiff-snapshots/README.md](kdiff-snapshots/README.md)
- **Helm Chart**: [kdiff-snapshots/helm-chart/README.md](kdiff-snapshots/helm-chart/README.md)
