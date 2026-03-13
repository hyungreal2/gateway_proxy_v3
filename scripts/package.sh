#!/usr/bin/env bash

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PROJECT_NAME="gateway-proxy"
VERSION="${1:-latest}"
OUTPUT="${PROJECT_ROOT}/${PROJECT_NAME}-${VERSION}.tar.gz"
TMP_OUTPUT="/tmp/${PROJECT_NAME}-${VERSION}.tar.gz"

tar -czf "${TMP_OUTPUT}" \
    --exclude='.git' \
    --exclude='.claude' \
    --exclude='.pytest_cache' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='*.egg-info' \
    --exclude='*.tar' \
    --exclude='*.tar.gz' \
    --exclude='logs/*.log' \
    -C "$(dirname "${PROJECT_ROOT}")" \
    "$(basename "${PROJECT_ROOT}")"

mv "${TMP_OUTPUT}" "${OUTPUT}"
echo "Packaged: ${OUTPUT}"
