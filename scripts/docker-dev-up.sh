#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
COMPOSE_FILE="$ROOT_DIR/docker-compose.dev.yml"
ENV_FILE="${COMPOSE_ENV_FILE:-$ROOT_DIR/.env.docker.local}"

compose_args=()
if [[ -f "$ENV_FILE" ]]; then
  compose_args+=(--env-file "$ENV_FILE")
else
  cat <<EOF
Warning: $ENV_FILE not found.
Create it from .env.docker.example before DB-backed API work:
  cp .env.docker.example .env.docker.local
  vi .env.docker.local

Continuing with docker-compose.dev.yml placeholder defaults.
EOF
fi
compose_args+=(-f "$COMPOSE_FILE")

docker compose "${compose_args[@]}" up --build -d
docker compose "${compose_args[@]}" ps

cat <<'EOF'

DW FX Ledger Docker Dev is running.

API:
http://127.0.0.1:8000/
http://127.0.0.1:8000/docs

Web:
http://localhost:3000/

Admin:
http://localhost:3001/

Logs:
docker compose -f docker-compose.dev.yml logs -f api
docker compose -f docker-compose.dev.yml logs -f web
docker compose -f docker-compose.dev.yml logs -f admin

Stop:
docker compose -f docker-compose.dev.yml down
EOF
