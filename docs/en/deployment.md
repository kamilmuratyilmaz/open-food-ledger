# Production Deployment Guide

The compose stack in this repo is for development. Before opening anything to the public, walk through the items below. Each one tells you **what** to do; **which tool** is up to you and your budget.

## 1. HTTPS is required

MCP client connectors (and public OAuth flows in general) won't complete a handshake over plain HTTP. Put a TLS terminator in front of the containers (managed cloud load balancer, reverse proxy container, or a tunnel service). Update `MCP_PUBLIC_URL` to that domain.

## 2. Get secrets out of compose

The hardcoded values today (DB password, `ALLOWED_ORIGINS`, `MCP_PUBLIC_URL`) shouldn't make it to production. Use a gitignored env file, Docker secrets, or your cloud provider's secret manager.

## 3. Move the frontend to a CDN

The current `frontend` container is a dev-grade Vite dev server. For production: build with `npm run build` and upload `dist/` to a static host (managed static-hosting service, your own CDN+bucket, your own nginx, etc.). Remove the `frontend` service from the production compose stack entirely.

## 4. Consider a managed database

If you self-host Postgres in compose, backups, replication, point-in-time recovery, and OS patching are all on you. A managed Postgres service handles most of that. If you stay self-hosted, at minimum do regular `pg_dump` + an offsite copy.

## 5. Run migrations as a deploy step

The repo already ships with Alembic (`migrations/` directory, `alembic.ini`). The compose api service runs `alembic upgrade head` before starting the app — fine for single-replica dev. For production:

- If you scale to multiple replicas, run the migration as a **separate CI/CD step** before the app boots. Replicas trying to upgrade simultaneously can race (Alembic uses advisory locks, but it's not bulletproof).
- If migration fails, halt the pipeline; don't start the app expecting a new schema.
- New migration: `uv run alembic revision --autogenerate -m "..."` after changing a model. The migration file goes into the PR for code review.

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
