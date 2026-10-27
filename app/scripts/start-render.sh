#!/bin/bash
set -euo pipefail

cd /app/server
gunicorn --bind 127.0.0.1:5100 --workers 2 --threads 4 --timeout 120 app:app &
api_pid=$!

cd /app/client
HOST=0.0.0.0 PORT="${PORT:-10000}" node dist/server/entry.mjs &
web_pid=$!

stop_services() {
  kill -TERM "$api_pid" "$web_pid" 2>/dev/null || true
  wait "$api_pid" 2>/dev/null || true
  wait "$web_pid" 2>/dev/null || true
}

trap stop_services TERM INT

set +e
wait -n "$api_pid" "$web_pid"
status=$?
set -e

stop_services
exit "$status"
