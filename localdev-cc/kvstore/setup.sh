#!/bin/bash

set -ex

ld+ exec aws-cli "./setup/dynamodb-kvstore.sh" || echo "DynamoDB already setup"
ld+ exec aws-cli "./setup/s3-kvstore.sh" || echo "S3 already setup"

ld+ reload-service kvstore