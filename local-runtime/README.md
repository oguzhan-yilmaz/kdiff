# create aws 
```bash
brew install minio

mkdir ~/minio-data

# http://localhost:9001 for minio web ui
minio server ~/minio-data --console-address ":9001"

# API: http://localhost:9000  http://127.0.0.1:9000
#    RootUser: minioadmin
#    RootPass: minioadmin
# WebUI: http://localhost:9001 http://127.0.0.1:9001
#    RootUser: minioadmin
#    RootPass: minioadmin


# aws cli access 
export AWS_ENDPOINT_URL_S3=http://localhost:9000  
export AWS_ACCESS_KEY_ID=minioadmin
export AWS_SECRET_ACCESS_KEY=minioadmin
export AWS_DEFAULT_REGION=us-east-1

# test minio access with aws cli

# create a bucket: 
aws s3 mb s3://test-bucket
echo "text here" > test.txt
aws s3 sync . s3://test-bucket
# aws s3 --endpoint-url http://localhost:9000 mb s3://test-bucket

aws s3 ls s3://test-bucket
```


# run kind cluster

```bash
kind create kdiffcluster



```

#

```bash



```
