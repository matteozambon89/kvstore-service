[![Build Image and Push to ECR](https://github.com/glg-public/kvstore-service/actions/workflows/build-and-push-to-ecr.yml/badge.svg)](https://github.com/glg-public/kvstore-service/actions/workflows/build-and-push-to-ecr.yml)

### Overview

Here comes the breakout of the kvstore service as a standalone service.

### Tests

Tests are provided by the [kvstore-service-tests](https://github.com/igroff/kvstore-service-tests) repository as the goal is a consistent set of interfaces, not a particular implementation.

### Custom AWS Endpoints

#### DynamoDB

Use the following environment variable:

- `KVSTORE_DYNAMO_HOST` only the hostname (e.g. `localhost`, `dynamodb-service` etc.)
- `KVSTORE_DYNAMO_PORT` only the port (e.g. `8000`)

#### S3

Use the following environment variable:

- `KVSTORE_S3_HOST` only the hostname (e.g. `localhost`, `localstack-service` etc.)
- `KVSTORE_S3_PORT` only the port (e.g. `4566`)
