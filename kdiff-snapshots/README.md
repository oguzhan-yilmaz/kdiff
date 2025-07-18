# kdiff-snapshots Helm Chart

A Helm chart for deploying kdiff-snapshots, a Kubernetes-native solution for generating comprehensive CSV snapshots of your Kubernetes cluster data using Steampipe.

## Installation

### From Helm Repository

```bash
# Add the repository
helm repo add kdiff-snapshots https://oguzhan-yilmaz.github.io/kdiff/

helm repo update kdiff-snapshots

# get the values on a file
helm show values kdiff-snapshots/kdiff-snapshots > kdiff.values.yaml

# Install with (hopefully updated) values file
helm upgrade --install \
  --namespace kdiff \
  --create-namespace \
  -f kdiff.values.yaml \
  kdiff-snapshots kdiff-snapshots/kdiff-snapshots
```

<!-- TODO: below ## Configuration section should be updated periodically -->

## Configuration

### Global Configuration

| Parameter                                      | Description                      | Default                              |
| ---------------------------------------------- | -------------------------------- | ------------------------------------ |
| `global.steampipeDatabasePassword`             | Database password for Steampipe  | `"Kj8mP2vN9xQ7tR5wL3cY1hB4nM6sD0pF"` |

### Debug Configuration

| Parameter | Description                    | Default |
| --------- | ------------------------------ | ------- |
| `debug`   | Enable debug mode (sleep infinity) | `false` |

### Steampipe Configuration

| Parameter                    | Description                      | Default                                  |
| ---------------------------- | -------------------------------- | ---------------------------------------- |
| `steampipe.replicaCount`     | Number of replicas               | `1`                                      |
| `steampipe.containerPort`    | Container port                   | `9193`                                   |
| `steampipe.image.repository` | Image repository                 | `ghcr.io/oguzhan-yilmaz/kdiff-snapshots` |
| `steampipe.image.pullPolicy` | Image pull policy                | `Always`                                 |
| `steampipe.image.tag`        | Image tag (overrides appVersion) | `""`                                     |
| `steampipe.imagePullSecrets` | Image pull secrets               | `[]`                                     |
| `steampipe.nameOverride`     | Name override                    | `"kdiff-snapshots"`                      |
| `steampipe.fullnameOverride` | Full name override               | `"kdiff-snapshots"`                      |

### Environment Variables

| Parameter                           | Description                               | Default        |
| ----------------------------------- | ----------------------------------------- | -------------- |
| `steampipe.envVars.INSTALL_PLUGINS` | Space-separated list of Steampipe plugins | `"kubernetes"` |
| `steampipe.envVars.AWS_PROFILE`     | AWS profile for AWS plugin                | `""`           |
| `steampipe.secretEnvVars`           | Secret environment variables              | `{}`           |

### Security Configuration

| Parameter                                | Description       | Default |
| ---------------------------------------- | ----------------- | ------- |
| `steampipe.securityContext.runAsUser`    | User ID           | `11234` |
| `steampipe.securityContext.runAsGroup`   | Group ID          | `11234` |
| `steampipe.securityContext.runAsNonRoot` | Run as non-root   | `true`  |
| `steampipe.podSecurityContext.fsGroup`   | File system group | `11234` |

### Service Configuration

| Parameter                | Description  | Default     |
| ------------------------ | ------------ | ----------- |
| `steampipe.service.type` | Service type | `ClusterIP` |
| `steampipe.service.port` | Service port | `9193`      |

### Resource Configuration

| Parameter                             | Description    | Default |
| ------------------------------------- | -------------- | ------- |
| `steampipe.resources.limits.cpu`      | CPU limit      | `""`    |
| `steampipe.resources.limits.memory`   | Memory limit   | `""`    |
| `steampipe.resources.requests.cpu`    | CPU request    | `""`    |
| `steampipe.resources.requests.memory` | Memory request | `""`    |

### Pod Configuration

| Parameter                    | Description                    | Default |
| ---------------------------- | ------------------------------ | ------- |
| `steampipe.podAnnotations`   | Pod annotations                | `{}`    |
| `steampipe.nodeSelector`     | Node selector                  | `{}`    |
| `steampipe.tolerations`      | Pod tolerations                | `[]`    |
| `steampipe.affinity`         | Pod affinity rules             | `{}`    |

### Credentials and Configuration

| Parameter                    | Description                                    | Default |
| ---------------------------- | ---------------------------------------------- | ------- |
| `steampipe.secretCredentials` | Secret credentials for kubeconfig, AWS, etc.   | `{}`    |
| `steampipe.config`           | Steampipe configuration files (.spc files)     | `{}`    |
| `steampipe.initDbSqlScripts` | SQL scripts to run during database initialization | `{}`    |

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


### Uninstall

```bash
# Uninstall and remove CRDs
helm uninstall my-kdiff --namespace kdiff
```
