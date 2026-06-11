#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.dev.yml"
ENV_FILE="${COMPOSE_ENV_FILE:-$ROOT_DIR/.env.docker.local}"

compose_args=()
if [[ -f "$ENV_FILE" ]]; then
  compose_args+=(--env-file "$ENV_FILE")
fi
compose_args+=(-f "$COMPOSE_FILE")

docker compose "${compose_args[@]}" ps
