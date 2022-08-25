#!/usr/bin/env sh

echo "Build Docker image..."
docker build -t kvstore:test .
