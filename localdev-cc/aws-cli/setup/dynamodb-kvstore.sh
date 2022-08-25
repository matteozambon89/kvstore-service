#!/bin/bash

set -ex

#! Alias to avoid having to pass endpoint-url every time
dynamodb="aws dynamodb --endpoint-url=$AWS_ENDPOINT_DYNAMODB"

#* DynamoDB - create "kvstore" table
$dynamodb create-table \
  --table-name kvstore \
  --attribute-definitions \
    AttributeName=path,AttributeType=S \
  --key-schema \
    AttributeName=path,KeyType=HASH \
  --provisioned-throughput \
    ReadCapacityUnits=10,WriteCapacityUnits=5

#* DynamoDB - set "kvstore" ttl
$dynamodb update-time-to-live \
  --table-name kvstore \
  --time-to-live-specification Enabled=true,AttributeName=ttl