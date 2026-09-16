#!/usr/bin/env bash
set -euo pipefail

docker compose --profile tools run --rm tests
