# snapshot maker


## get req. env vars
```bash

source ./.env

printenv | grep -E "AWS|BUCKET_" 

aws s3 ls s3://$BUCKET_NAME
```


## run kind cluster for testing

```bash
export KDIFF_TEST_CLUSTER_NAME="kdiff-helm-install"
export KDIFF_KUBECONFIG_FILE="$HOME/.kube/kdiff-tests"

kind create cluster \
    --kubeconfig "$KDIFF_KUBECONFIG_FILE" \
    --image "kindest/node:v1.34.0" \
    --name "$KDIFF_TEST_CLUSTER_NAME" 

export KUBECONFIG="$KDIFF_KUBECONFIG_FILE"
export KUBE_CONTEXT="kind-$KDIFF_TEST_CLUSTER_NAME"

echo "current context: $(kubectl config current-context)"
echo "current cluster-info: $(kubectl cluster-info)"

kubectl get pod -A 
```


#

```bash


# helm upgrade --install \
helm install \
  --namespace default \
  --create-namespace \
  -f ../kdiff-snapshots/kdiff.values.yaml \
  kdiff-snapshots ../kdiff-snapshots/helm-chart/

helm uninstall -n default kdiff-snapshots

```

#

```bash



```
