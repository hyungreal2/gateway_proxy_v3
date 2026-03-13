#!/usr/bin/env bash

set -e

conda run -n myenv pytest "$@"
