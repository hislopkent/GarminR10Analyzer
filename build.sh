#!/usr/bin/env bash
# Build the Docker image without using cache to avoid BuildKit lease errors.
docker build --no-cache -t garmin-r10-analyzer .
