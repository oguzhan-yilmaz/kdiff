# kdiff-snapshots Helm Chart

A Helm chart for deploying kdiff-snapshots, a Kubernetes-native solution for generating comprehensive CSV snapshots of your Kubernetes cluster data using Steampipe.

## Installation

### From Helm Repository

```bash
# Add the repository
helm repo add kdiff-snapshots https://oguzhan-yilmaz.github.io/kdiff/
helm repo update

# Install the chart
helm install kdiff-snapshots kdiff-snapshots/kdiff-snapshots
```

### Using ArgoCD

```bash
# Apply the ArgoCD application
kubectl apply -f argocd-application.yaml
```

## Configuration

### Global Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `global.steampipeDatabasePassword` | Database password for Steampipe | `"Kj8mP2vN9xQ7tR5wL3cY1hB4nM6sD0pF"` |
| `global.steampipeCreateReadOnlyServiceAccount` | Enable read-only service account | `true` |

### Steampipe Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `steampipe.replicaCount` | Number of replicas | `1` |
| `steampipe.containerPort` | Container port | `9193` |
| `steampipe.image.repository` | Image repository | `ghcr.io/oguzhan-yilmaz/kdiff-snapshots` |
| `steampipe.image.pullPolicy` | Image pull policy | `Always` |
| `steampipe.image.tag` | Image tag (overrides appVersion) | `""` |
| `steampipe.imagePullSecrets` | Image pull secrets | `[]` |
| `steampipe.nameOverride` | Name override | `"kdiff-snapshots"` |
| `steampipe.fullnameOverride` | Full name override | `"kdiff-snapshots"` |

### Environment Variables

| Parameter | Description | Default |
|-----------|-------------|---------|
| `steampipe.envVars.INSTALL_PLUGINS` | Space-separated list of Steampipe plugins | `"kubernetes"` |
| `steampipe.envVars.AWS_PROFILE` | AWS profile for AWS plugin | `""` |
| `steampipe.secretEnvVars` | Secret environment variables | `{}` |

### Security Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `steampipe.securityContext.runAsUser` | User ID | `11234` |
| `steampipe.securityContext.runAsGroup` | Group ID | `11234` |
| `steampipe.securityContext.runAsNonRoot` | Run as non-root | `true` |
| `steampipe.podSecurityContext.fsGroup` | File system group | `11234` |

### Service Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `steampipe.service.type` | Service type | `ClusterIP` |
| `steampipe.service.port` | Service port | `9193` |

### Resource Configuration

| Parameter | Description | Default |
|-----------|-------------|---------|
| `steampipe.resources.limits.cpu` | CPU limit | `""` |
| `steampipe.resources.limits.memory` | Memory limit | `""` |
| `steampipe.resources.requests.cpu` | CPU request | `""` |
| `steampipe.resources.requests.memory` | Memory request | `""` |


## Configuration Examples

### Basic Installation

```yaml
# values.yaml
global:
  steampipeDatabasePassword: "my-secure-password"
  steampipeCreateReadOnlyServiceAccount: true

steampipe:
  replicaCount: 1
  envVars:
    INSTALL_PLUGINS: "kubernetes"
```

### Multi-Cloud Setup

```yaml
# values.yaml
steampipe:
  envVars:
    INSTALL_PLUGINS: "kubernetes aws gcp azure"
    AWS_PROFILE: "production"
    GCP_PROJECT: "my-gcp-project"
  
  secretEnvVars:
    AWS_ACCESS_KEY_ID: "your-aws-key"
    AWS_SECRET_ACCESS_KEY: "your-aws-secret"
    GOOGLE_APPLICATION_CREDENTIALS: "your-gcp-key"
  
  config:
    aws.spc: |
      connection "aws" {
        plugin  = "aws"
        profile = "production"
        regions = ["us-west-2", "us-east-1"]
      }
    
    gcp.spc: |
      connection "gcp" {
        plugin  = "gcp"
        project = "my-gcp-project"
      }
```

### Custom Kubeconfig

```yaml
# values.yaml
steampipe:
  secretCredentials:
    - name: kubeconfig
      directory: ".kube"
      filename: "config"
      content: |
        apiVersion: v1
        kind: Config
        clusters:
        - name: production-cluster
          cluster:
            server: https://api.production.example.com
            certificate-authority-data: LS0tLS1CRUdJTi...
        contexts:
        - name: production-context
          context:
            cluster: production-cluster
            user: production-user
        current-context: production-context
        users:
        - name: production-user
          user:
            token: your-service-account-token
  
  config:
    kubernetes.spc: |
      connection "kubernetes" {
        plugin         = "kubernetes"
        config_path    = "~/.kube/config"
        config_context = "production-context"
        source_types   = ["deployed"]
      }
```

## Usage

### Installation Commands

```bash
# Install with custom values
helm install my-kdiff kdiff-snapshots/kdiff-snapshots \
  --set steampipe.envVars.INSTALL_PLUGINS="kubernetes aws"

# Install with values file
helm install my-kdiff kdiff-snapshots/kdiff-snapshots -f values.yaml

# Install in specific namespace
helm install my-kdiff kdiff-snapshots/kdiff-snapshots \
  --namespace steampipe \
  --create-namespace
```

### Upgrade Commands

```bash
# Upgrade with new values
helm upgrade my-kdiff kdiff-snapshots/kdiff-snapshots \
  --set steampipe.image.tag="latest"

# Upgrade with values file
helm upgrade my-kdiff kdiff-snapshots/kdiff-snapshots -f values.yaml
```

### Uninstall Commands

```bash
# Uninstall the release
helm uninstall my-kdiff

# Uninstall and remove CRDs
helm uninstall my-kdiff --cascade=foreground
```
