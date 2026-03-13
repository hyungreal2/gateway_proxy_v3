#!/usr/bin/env bash

set -e

IMAGE_NAME="gateway-proxy"
IMAGE_TAG="${1:-latest}"

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "Error: .env file not found at ${ENV_FILE}"
    echo "Copy .env.example to .env and fill in your values."
    exit 1
fi

podman run \
    --env-file "${ENV_FILE}" \
    -v "${SCRIPT_DIR}/logs:/app/logs" \
    -p 8080:8080 \
    "${IMAGE_NAME}:${IMAGE_TAG}"
