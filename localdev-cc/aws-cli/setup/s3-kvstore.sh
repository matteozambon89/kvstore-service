#!/bin/bash

set -ex

#! Alias to avoid having to pass endpoint-url every time
s3api="aws s3api --endpoint-url=$AWS_ENDPOINT_LOCALSTACK"

$s3api create-bucket --bucket=kvstore