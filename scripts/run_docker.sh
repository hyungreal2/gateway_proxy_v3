#!/usr/bin/env bash

set -e

IMAGE_NAME="gateway-proxy"
IMAGE_TAG="${1:-latest}"

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo ".env not found, copying from .env.example ..."
    cp "${SCRIPT_DIR}/.env.example" "${ENV_FILE}"
fi

docker run \
    --env-file "${ENV_FILE}" \
    -v "${SCRIPT_DIR}/logs:/app/logs" \
    -p 8080:8080 \
    "${IMAGE_NAME}:${IMAGE_TAG}"
