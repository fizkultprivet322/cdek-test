#!/usr/bin/env bash

set -euo pipefail

SERVICE_URL="${SERVICE_URL:-http://localhost:8000/}"
CHECK_INTERVAL_SECONDS="${CHECK_INTERVAL_SECONDS:-30}"
LOG_FILE="${LOG_FILE:-./autoheal.log}"

touch "${LOG_FILE}"

echo "Autoheal started. Monitoring ${SERVICE_URL} every ${CHECK_INTERVAL_SECONDS}s."

while true; do
  if ! curl -fsS --max-time 5 "${SERVICE_URL}" >/dev/null; then
    timestamp="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
    echo "${timestamp} service unavailable; running docker compose restart" >>"${LOG_FILE}"
    docker compose restart
  fi
  sleep "${CHECK_INTERVAL_SECONDS}"
done
