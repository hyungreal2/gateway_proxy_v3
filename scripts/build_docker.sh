#!/usr/bin/env bash

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
IMAGE_NAME="gateway-proxy"
IMAGE_TAG="${1:-latest}"
OUTPUT_FILE="${SCRIPT_DIR}/${IMAGE_NAME}-${IMAGE_TAG}.tar"

echo "Building image ${IMAGE_NAME}:${IMAGE_TAG} ..."
docker build -f "${SCRIPT_DIR}/docker/Dockerfile" -t "${IMAGE_NAME}:${IMAGE_TAG}" "${SCRIPT_DIR}"

echo "Saving image to ${OUTPUT_FILE} ..."
docker save -o "${OUTPUT_FILE}" "${IMAGE_NAME}:${IMAGE_TAG}"

echo "Done: ${OUTPUT_FILE}"
echo ""
echo "To load on the target host:"
echo "  docker load -i ${OUTPUT_FILE}"
echo ""
echo "To run:"
echo "  cp .env.example .env  # edit as needed"
echo "  docker run --env-file .env -v ./logs:/app/logs -p 8080:8080 ${IMAGE_NAME}:${IMAGE_TAG}"
