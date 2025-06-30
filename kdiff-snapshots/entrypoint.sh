#!/bin/bash

# Get the current date and time
DATE=$(date +%Y-%m-%d)

# Get the current time
TIME=$(date +%H-%M-%S)

# Get the current user
USER=$(whoami)

echo "Date: $DATE"
echo "Time: $TIME"
echo "User: $USER"

bash csv-script.sh --debug --out-dir /tmp/kdiff-snapshots

ls -al /tmp/kdiff-snapshots
