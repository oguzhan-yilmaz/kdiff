#!/bin/bash

# Start steampipe service
steampipe service start || true

# Wait for healthcheck to succeed
WAIT_TIME=0
while true; do
    if bash healthcheck.sh; then
        echo "Steampipe service is healthy after waiting ${WAIT_TIME} seconds"
        break
    fi
    echo "Waiting for steampipe service to be healthy... (${WAIT_TIME} seconds elapsed)"
    WAIT_TIME=$((WAIT_TIME + 1))
    sleep 1
done
