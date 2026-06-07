#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
STATE_DIR="$ROOT_DIR/.dev"
QUIET="${1:-}"

kill_tree() {
  local pid="$1"
  local signal="${2:-TERM}"
  local child

  [[ -n "$pid" ]] || return
  kill -0 "$pid" 2>/dev/null || return

  for child in $(pgrep -P "$pid" 2>/dev/null || true); do
    kill_tree "$child" "$signal"
  done

  kill "-$signal" "$pid" 2>/dev/null || true
}

wait_pid_gone() {
  local pid="$1"

  for _ in {1..20}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      return
    fi
    sleep 0.2
  done
}

port_pids() {
  local port="$1"
  local pids

  pids="$(node "$ROOT_DIR/scripts/dev-port-pids.js" "$port" 2>/dev/null || true)"
  if [[ -z "$pids" ]] && command -v lsof >/dev/null 2>&1; then
    pids="$(lsof -nP -iTCP:"$port" -sTCP:LISTEN -t 2>/dev/null || true)"
  fi
  printf '%s\n' "$pids"
}

stop_service() {
  local name="$1"
  local pid_file="$STATE_DIR/$name.pid"

  if [[ ! -f "$pid_file" ]]; then
    [[ "$QUIET" == "--quiet" ]] || echo "$name is not managed as running"
    return
  fi

  local stopped=0
  local pid
  for pid in $(cat "$pid_file"); do
    if [[ -n "$pid" ]] && kill -0 "$pid" 2>/dev/null; then
      kill_tree "$pid" "TERM"
      wait_pid_gone "$pid"
      if kill -0 "$pid" 2>/dev/null; then
        kill_tree "$pid" "KILL"
      fi
      stopped=1
    fi
  done

  if [[ "$stopped" == "1" ]]; then
    [[ "$QUIET" == "--quiet" ]] || echo "$name stopped"
  else
    [[ "$QUIET" == "--quiet" ]] || echo "$name pid file was stale"
  fi

  rm -f "$pid_file"
}

stop_service "api"
stop_service "web"
stop_service "admin"

stop_port() {
  local name="$1"
  local port="$2"
  local pids

  pids="$(port_pids "$port")"
  if [[ -z "$pids" ]]; then
    return
  fi

  while read -r pid; do
    [[ -z "$pid" ]] && continue
    kill_tree "$pid" "TERM"
  done <<< "$pids"

  for _ in {1..20}; do
    pids="$(port_pids "$port")"
    [[ -z "$pids" ]] && break
    sleep 0.2
  done

  pids="$(port_pids "$port")"
  if [[ -n "$pids" ]]; then
    while read -r pid; do
      [[ -z "$pid" ]] && continue
      kill_tree "$pid" "KILL"
    done <<< "$pids"
  fi

  [[ "$QUIET" == "--quiet" ]] || echo "$name port $port cleared"
}

stop_port "api" "8000"
stop_port "web" "3000"
stop_port "admin" "3001"
