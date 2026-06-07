#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$ROOT_DIR/.dev"
LOG_DIR="$STATE_DIR/logs"
mkdir -p "$LOG_DIR"

"$ROOT_DIR/scripts/dev-stop.sh" --quiet

port_pids() {
  local port="$1"
  local pids

  pids="$(node "$ROOT_DIR/scripts/dev-port-pids.js" "$port" 2>/dev/null || true)"
  if [[ -z "$pids" ]] && command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
  fi
  printf '%s\n' "$pids"
}

wait_for_port_clear() {
  local name="$1"
  local port="$2"
  local pids

  for _ in {1..30}; do
    pids="$(port_pids "$port")"
    if [[ -z "$pids" ]]; then
      return
    fi
    sleep 0.2
  done

  echo "$name port $port is still in use:"
  port_pids "$port" || true
  exit 1
}

wait_for_port_clear "api" "8000"
wait_for_port_clear "web" "3000"
wait_for_port_clear "admin" "3001"

node - <<'NODE' "$ROOT_DIR"
const fs = require("fs");
const path = require("path");

const root = process.argv[2];
for (const relative of ["apps/web/.next", "apps/admin/.next"]) {
  const target = path.join(root, relative);
  fs.rmSync(target, { force: true, recursive: true });
  console.log(`cleaned ${relative}`);
}
NODE

start_service() {
  local name="$1"
  local workdir="$2"
  local command="$3"
  local pid_file="$STATE_DIR/$name.pid"
  local log_file="$LOG_DIR/$name.log"

  (
    cd "$workdir"
    nohup setsid bash -lc "exec $command" >"$log_file" 2>&1 < /dev/null &
    echo $! >"$pid_file"
  )

  local pid
  pid="$(cat "$pid_file")"
  echo "$name starting launcher_pid=$pid log=$log_file"
}

start_service "api" "$ROOT_DIR/apps/api" "uv run uvicorn app.main:app --reload"
start_service "web" "$ROOT_DIR" "pnpm dev:web"
start_service "admin" "$ROOT_DIR" "pnpm dev:admin"

record_port_pids() {
  local name="$1"
  local port="$2"
  local pid_file="$STATE_DIR/$name.pid"
  local pids

  pids="$(port_pids "$port")"
  pids="${pids//$'\n'/ }"
  if [[ -n "$pids" ]]; then
    echo "$pids" >"$pid_file"
    echo "$name listening port=$port pids=$pids"
  fi
}

wait_for_url() {
  local name="$1"
  local url="$2"
  local log_file="$LOG_DIR/$name.log"

  if ! command -v curl >/dev/null 2>&1; then
    return
  fi

  for _ in {1..60}; do
    if curl -fsS --max-time 2 "$url" >/dev/null 2>&1; then
      echo "$name ready $url"
      return
    fi
    sleep 1
  done

  echo "$name did not respond within 60s: $url"
  echo "last log lines for $name:"
  tail -n 80 "$log_file" 2>/dev/null || true
  exit 1
}

wait_for_url "api" "http://127.0.0.1:8000/health"
record_port_pids "api" "8000"
wait_for_url "web" "http://localhost:3000"
record_port_pids "web" "3000"
wait_for_url "admin" "http://localhost:3001"
record_port_pids "admin" "3001"

cat <<EOF

All dev services are starting in the background.

API   http://127.0.0.1:8000
Web   http://localhost:3000
Admin http://localhost:3001

Logs:
  tail -f .dev/logs/api.log
  tail -f .dev/logs/web.log
  tail -f .dev/logs/admin.log
EOF
