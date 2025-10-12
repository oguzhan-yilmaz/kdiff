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



### From Helm Repository (LOCALLY)

```bash
git clone https://github.com/oguzhan-yilmaz/kdiff

cd kdiff/kdiff-snapshots
```

```bash
# get the values on a file
helm show values helm-chart/ > kdiff.values.yaml

vim kdiff.values.yaml

# Install with (hopefully updated) values file
helm upgrade --install \
  --namespace kdiff \
  --create-namespace \
  -f kdiff.values.yaml \
  kdiff-snapshots helm-chart/


helm uninstall -n kdiff kdiff-snapshots
```


## Configuration
