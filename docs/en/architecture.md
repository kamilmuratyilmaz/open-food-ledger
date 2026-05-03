# Architecture

## Components

```
                  Browser                   Claude Desktop      ChatGPT
                     │                           │                 │
                     │ http                      │ stdio           │ OAuth + bearer
                     ▼                           │                 │
   ┌─────────────────────────────┐ ◀ :5173       │                 │
   │  frontend  (Vite dev)       │               │                 │
   │  ─ React SPA + HMR          │               │                 │
   │  ─ /api/* proxy → api:8000  │  (vite.config) │                 │
   └─────────────┬───────────────┘               │                 │
                 │                               │                 │
                 ▼                               ▼                 ▼
   ┌─────────────────────────────┐ ◀ :8000   ┌──────────────────────────┐ ◀ :8001
   │  api  (FastAPI)             │           │  mcp  (FastMCP container)│
   │  /api/auth/*                │           │  /mcp                    │
   │  /api/entries/*             │           │  /authorize, /token      │
   │  /api/analytics/*           │           │  /oauth/login            │
   │  /api/export/*              │           │  /.well-known/*          │
   │  /docs                      │           └────────────┬─────────────┘
   └─────────────┬───────────────┘                        │
                 │                            FOOD_API_URL=http://api:8000
                 │                                        │
                 └──────────────┬─────────────────────────┘
                                ▼
                  ┌─────────────────────────────┐ ◀ :5432
                  │  db  (PostgreSQL 16)        │
                  │  users, food_entries        │
                  └─────────────────────────────┘
```

Two compose files:

- **`compose.dev.yml`** — brings up four containers: **frontend** (Vite dev server, HMR), **api** (FastAPI `target: dev`, `--reload`, source bind mount), **mcp** (FastMCP HTTP + OAuth, source bind mount), **db** (Postgres). Run with `docker compose -f compose.dev.yml up --build`.
- **`compose.prod.yml`** — three containers: **api** (`target: prod`, source baked, no reload, no bind mount), **mcp** (image-baked source), **db**. No frontend — production deploys the static build to a CDN / static host via CI/CD. Run with `docker compose -f compose.prod.yml up --build -d`.

The dev/prod difference is enforced by the `Dockerfile`'s multi-stage layout (`base` → `dev` → `prod`). `dev` and `prod` share all layers and differ only in their `CMD` — one adds `--reload`, the other doesn't. The MCP container reaches the API via compose internal DNS (`FOOD_API_URL=http://api:8000`); `MCP_PUBLIC_URL` is the user-facing URL (locally `http://localhost:8001`, in production your public domain).

## Auth model

Deliberately simple:

- Each user receives a **single** `api_token` on registration (`secrets.token_urlsafe(32)`)
- Stored in the `users.api_token` column with a unique index
- The SPA keeps it in `localStorage`, the MCP server reads it from env or the request header, OAuth clients hold it as access_token — **all the same token**
- Token rotation: `POST /api/me/rotate-token` invalidates all active channels
- No JWT, no refresh tokens, no session management

**Upside:** low cognitive overhead, easy to debug. **Downside:** no scopes (every token has full access), no expiration (lives until you rotate).

## Data schema

```sql
users:
  id              uuid PRIMARY KEY
  email           text UNIQUE NOT NULL
  password_hash   text NOT NULL                   -- bcrypt
  api_token       text UNIQUE NOT NULL            -- secrets.token_urlsafe(32)
  created_at      timestamptz DEFAULT now()

food_entries:
  id          uuid PRIMARY KEY
  user_id     uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE
  entry_date  date NOT NULL
  entry_time  text NOT NULL                       -- 'HH:MM'
  meal_type   text NOT NULL                       -- breakfast|lunch|dinner|snack
  food_name   text NOT NULL
  weight_g    numeric NOT NULL
  calories    numeric DEFAULT 0
  protein_g   numeric DEFAULT 0
  carbs_g     numeric DEFAULT 0
  fat_g       numeric DEFAULT 0
  fiber_g     numeric DEFAULT 0
  sugar_g     numeric DEFAULT 0
  sodium_mg   numeric DEFAULT 0
  notes       text
  created_at  timestamptz DEFAULT now()
```

Tables are managed by Alembic (`migrations/` directory, `alembic.ini`). The compose api service runs `alembic upgrade head` before starting the app — application code has no `create_all` or lifespan hook. Schema changes: edit the model, run `uv run alembic revision --autogenerate -m "..."`, the migration file lands in the PR for code review.

## Stack detail

- **FastAPI 0.115+** — REST API
- **SQLAlchemy 2.0** (sync) — ORM
- **psycopg 3** — Postgres driver
- **bcrypt 4.2+** — password hashing
- **openpyxl 3.1+** — XLSX export
- **pydantic 2** — request/response validation
- **PostgreSQL 16** — DB
- **mcp 1.27+** — MCP protocol implementation via FastMCP

Frontend: React 18 + Vite 5 + TypeScript, source under `frontend/src/` organized by feature folders:

- `frontend/src/features/{auth,entries,analytics,settings}/` — domain components
- `frontend/src/components/` — cross-feature UI (Masthead, ToastHost)
- `frontend/src/context/AuthContext.tsx` — token + user state, login/register/signOut/rotateToken
- `frontend/src/hooks/{useEntries,useToast}.ts` — data fetching + global toast queue
- `frontend/src/lib/{api,storage,format}.ts` — fetch client (Bearer + 401 handling), localStorage, formatting helpers
- `frontend/src/types/api.ts` — TypeScript types mirroring the Pydantic schemas

State management is minimal: AuthContext (cross-cutting) + useState (UI state) + custom hooks (server state). No Redux/Zustand/TanStack Query. Navigation is modal-based (auth screen ↔ app shell, settings slide-out) — no react-router.

The Vite dev container bind-mounts `frontend/` for HMR and serves at `:5173`. Production deployment (static build → CDN/static host) is out of scope for this repo. Single global stylesheet at `frontend/src/styles.css` (paper/ink palette, Fraunces + DM Sans + JetBrains Mono).

## Security

- **Passwords** are hashed with bcrypt; never stored plaintext
- **API tokens** are generated via `secrets.token_urlsafe(32)` (256 bits of entropy)
- **OAuth flow** requires PKCE S256 (plain method is rejected)
- **DB cascade delete** — deleting a user removes their entries
- **CORS** is fine because the SPA is served from the same origin in dev. If you serve the frontend from a different origin in production, tighten `ALLOWED_ORIGINS`
- **No rate limiting** — recommended before any public deployment, especially on login/register endpoints
- **No email verification** — add SMTP integration before opening public registration

## Deployment notes

Minimum for a public deployment:

- HTTPS (reverse proxy or cloud LB)
- `MCP_PUBLIC_URL` env set to the public domain (used in OAuth metadata)
- Postgres backup strategy
- `POSTGRES_PASSWORD` from env / secret manager, never hardcoded
- Network isolation between containers

For multi-replica deployments, move OAuth state out of in-memory dicts in `mcp_server/oauth.py` (Redis or Postgres tables).

See [deployment.md](deployment.md) for the full guide.
