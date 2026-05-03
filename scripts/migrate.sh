#!/usr/bin/env bash
#
# Apply pending Alembic migrations against the configured database, as a
# one-off step that runs BEFORE rolling out the application containers.
#
# Why a separate step:
#   - In multi-replica deployments, every api container racing on
#     `alembic upgrade head` simultaneously can corrupt the schema or the
#     alembic_version table. Alembic uses an advisory lock but it is not
#     a 100% guarantee under connection failures / split-brain.
#   - If the migration fails, the pipeline aborts here — no app container
#     boots expecting a schema that does not exist.
#
# Pipeline order:
#   1. Build & push new images
#   2. ./scripts/migrate.sh                         <-- this script
#   3. docker compose -f compose.prod.yml up -d     (rolling update)
#
# Environment overrides:
#   COMPOSE_FILE   path to the compose file (default: compose.prod.yml)
#   COMPOSE_SERVICE service whose image owns alembic.ini + migrations/
#                  (default: api)
#
# Exits non-zero on migration failure.

set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-compose.prod.yml}"
COMPOSE_SERVICE="${COMPOSE_SERVICE:-api}"

if [[ ! -f "$COMPOSE_FILE" ]]; then
  echo "error: compose file '$COMPOSE_FILE' not found" >&2
  echo "       set COMPOSE_FILE env to point at a different file" >&2
  exit 2
fi

echo ">> Applying Alembic migrations via $COMPOSE_FILE ($COMPOSE_SERVICE)"

# `run --rm` spawns a one-off container with the same image and env as
# the service, but overrides the command to alembic only — no uvicorn,
# no app boot. Dependencies (db) come up automatically if not running.
docker compose -f "$COMPOSE_FILE" run --rm "$COMPOSE_SERVICE" alembic upgrade head

echo ">> Migrations applied successfully. Safe to roll out the api service."
