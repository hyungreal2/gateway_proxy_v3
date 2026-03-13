#!/usr/bin/env bash

set -e

conda run -n myenv uvicorn gateway_proxy.main:app \
    --host 0.0.0.0 \
    --port 8080 \
    --workers 4
