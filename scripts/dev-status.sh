#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$ROOT_DIR/.dev"

status_service() {
  local name="$1"
  local port="$2"
  local pid_file="$STATE_DIR/$name.pid"
  local pids

  pids="$(node "$ROOT_DIR/scripts/dev-port-pids.js" "$port" 2>/dev/null || true)"
  if [[ -z "$pids" ]] && command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
  fi
  pids="${pids//$'\n'/ }"

  if [[ -n "$pids" ]]; then
    echo "$name running port=$port pids=$pids"
    return
  fi

  if [[ -f "$pid_file" ]]; then
    echo "$name stopped stale_pid_file=$(cat "$pid_file")"
  else
    echo "$name stopped"
  fi
}

status_service "api" "8000"
status_service "web" "3000"
status_service "admin" "3001"
