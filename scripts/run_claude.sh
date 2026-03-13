#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${SCRIPT_DIR}/.env"

# Load .env if present
if [[ -f "${ENV_FILE}" ]]; then
    set -a
    source "${ENV_FILE}"
    set +a
fi

GATEWAY_URL="${GATEWAY_URL:-http://localhost:8080}"

ANTHROPIC_BASE_URL="${GATEWAY_URL}" claude "$@"
