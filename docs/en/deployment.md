# Production Deployment Guide

The compose stack in this repo is for development. Before opening anything to the public, walk through the items below. Each one tells you **what** to do; **which tool** is up to you and your budget.

## 1. HTTPS is required

MCP client connectors (and public OAuth flows in general) won't complete a handshake over plain HTTP. Put a TLS terminator in front of the containers (managed cloud load balancer, reverse proxy container, or a tunnel service). Update `MCP_PUBLIC_URL` to that domain.

## 2. Get secrets out of compose

`compose.prod.yml` now reads from `.env.prod` (via `env_file:` directives). Before your first deploy:

```bash
cp .env.prod.example .env.prod
# edit .env.prod: real POSTGRES_PASSWORD, DATABASE_URL, ALLOWED_ORIGINS, MCP_PUBLIC_URL
```

`.env.prod` is in `.gitignore` (never committed); `.env.prod.example` is a template that lives in the repo. For tougher setups: inject env vars from your cloud's secret manager (AWS Secrets Manager, Vault, etc.) at deploy time so `.env.prod` never touches disk.

## 3. Move the frontend to a CDN

The current `frontend` container is a dev-grade Vite dev server. For production: build with `npm run build` and upload `dist/` to a static host (managed static-hosting service, your own CDN+bucket, your own nginx, etc.). Remove the `frontend` service from the production compose stack entirely.

## 4. Consider a managed database

If you self-host Postgres in compose, backups, replication, point-in-time recovery, and OS patching are all on you. A managed Postgres service handles most of that. If you stay self-hosted, at minimum do regular `pg_dump` + an offsite copy.

## 5. Run migrations as a deploy step

The repo ships with Alembic (`migrations/` directory, `alembic.ini`). On the single-replica dev/prod stacks the api container runs `alembic upgrade head` on boot — fine.

**Once you scale to multiple replicas** (2+ api copies behind a load balancer): if all of them race on `alembic upgrade head` at the same time, they can corrupt the schema or the alembic_version table. Alembic uses a Postgres advisory lock but it isn't a 100% guarantee. So the migration must run **separately from container boot**, as a deploy step.

A ready-to-use script ships with the repo:

```bash
./scripts/migrate.sh
```

It spins up a one-off container (same image as the api service, but with `alembic upgrade head` instead of uvicorn), runs the migration, exits, and cleans itself up. Idempotent — a no-op when there are no pending migrations.

**CI/CD pipeline order:**
1. Build & push the new image to the registry
2. `./scripts/migrate.sh` (pointed at the production DB via env)
3. If step 2 fails, abort the pipeline — don't start the app expecting a schema that isn't there; users would get 500s
4. If step 2 succeeds, roll out the new api containers (the migration is already applied, so they only need to run uvicorn)

When you actually go multi-replica: drop the `alembic upgrade head &&` prefix from the prod compose api `command:` and leave only uvicorn — the script handles migrations.

**Adding a new migration (dev workflow):**
```bash
# 1. Change the model (e.g., add a column in app/db/models.py)
# 2. Generate the migration
uv run alembic revision --autogenerate -m "add display_name to users"
# 3. Commit migrations/versions/xxx_add_display_name_to_users.py with the PR
# 4. The reviewer reads the migration file as part of the diff
```

## 6. Add rate limiting

`/api/auth/login`, `/api/auth/register`, and `/oauth/login` are open to brute-force attacks. Add a rate-limit middleware for FastAPI and apply tight limits (e.g., 5 requests per minute) on those specific endpoints.

## 7. Tighten CORS

`ALLOWED_ORIGINS=*` → your actual frontend domain. Comma-separate if you have several.

## 8. Error tracking

Add at least an error tracker (any cloud-managed service) so application errors aren't silently swallowed. Switching to structured (JSON) logging makes integration with log aggregators easier.

## 9. Restrict the network

Review the port mappings in compose: only the TLS terminator should be publicly exposed. Keep `api` (:8000), `mcp` (:8001), and `db` (:5432) internal — inter-container traffic already works over compose's internal DNS.

## 10. Container hygiene

- Pin image tags (don't use `latest`)
- Wire image scanning into CI
- `restart: unless-stopped`, resource limits (memory/cpu), log driver size limits
- Push images to a registry; separate build from deploy

## 11. Privacy / TOS

A food log is potentially health-related data. Add privacy policy + TOS pages to the SPA, give users a "delete my account" button (cascade delete already works — you only need an endpoint), and data export already exists (`GET /api/export/xlsx`). Check your jurisdiction's GDPR/CCPA/KVKK obligations.

## 12. OAuth state

`mcp_server/oauth.py` keeps `_clients` and `_codes` in memory. That's fine on a single replica (clients re-register after a restart; the user just sees one extra login). If you scale to multiple replicas, move that state to a shared store (a Postgres table or an in-memory cache service).

---

## Suggested order

If you can only do five things, do these first: **HTTPS → secrets out of compose → migration tool → rate limiting → error tracker.** That covers the standard risks of a small production setup. The rest scales with traffic and user count.
