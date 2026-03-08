#!/usr/bin/env bash
set -euo pipefail

PORT="${MLFLOW_PORT:-5001}"
HOST="${MLFLOW_HOST:-0.0.0.0}"
BACKEND_STORE_URI="${MLFLOW_BACKEND_STORE_URI:-./ml/mlruns}"

kill_port() {
  local port="$1"

  if ! command -v lsof >/dev/null 2>&1; then
    echo "lsof is required to stop existing processes on port ${port}."
    return 1
  fi

  local pids
  pids="$(lsof -ti "tcp:${port}" || true)"
  if [[ -z "${pids}" ]]; then
    return 0
  fi

  echo "Stopping existing process(es) on port ${port}: ${pids}"
  kill -TERM ${pids} 2>/dev/null || true

  local i
  for i in {1..20}; do
    if lsof -ti "tcp:${port}" >/dev/null 2>&1; then
      sleep 0.2
    else
      return 0
    fi
  done

  echo "Force killing remaining process(es) on port ${port}: ${pids}"
  kill -KILL ${pids} 2>/dev/null || true
}

mkdir -p "${BACKEND_STORE_URI}"

kill_port "${PORT}"

echo "Starting MLflow server on http://${HOST}:${PORT}"
exec python3 -m mlflow server \
  --host "${HOST}" \
  --port "${PORT}" \
  --backend-store-uri "${BACKEND_STORE_URI}" \
  --allowed-hosts "*" \
  --cors-allowed-origins "*"
