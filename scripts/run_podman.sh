#!/usr/bin/env bash

set -e

IMAGE_NAME="gateway-proxy"
IMAGE_TAG="${1:-latest}"

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"

podman run \
    -e VLLM_BASE_URL="${VLLM_BASE_URL:-http://localhost:8080}" \
    -v "${SCRIPT_DIR}/logs:/app/logs" \
    -p 8080:8080 \
    "${IMAGE_NAME}:${IMAGE_TAG}"
