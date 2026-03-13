#!/usr/bin/env bash

set -e

IMAGE_NAME="gateway-proxy"
IMAGE_TAG="${1:-latest}"
OUTPUT_FILE="${IMAGE_NAME}-${IMAGE_TAG}.tar"

echo "Building image ${IMAGE_NAME}:${IMAGE_TAG} ..."
docker build -f docker/Dockerfile -t "${IMAGE_NAME}:${IMAGE_TAG}" .

echo "Saving image to ${OUTPUT_FILE} ..."
docker save -o "${OUTPUT_FILE}" "${IMAGE_NAME}:${IMAGE_TAG}"

echo "Done: ${OUTPUT_FILE}"
echo ""
echo "To load on the target host:"
echo "  docker load -i ${OUTPUT_FILE}"
echo ""
echo "To run (override VLLM_BASE_URL as needed):"
echo "  docker run -e VLLM_BASE_URL=http://<host>:<port> -p 8080:8080 ${IMAGE_NAME}:${IMAGE_TAG}"
