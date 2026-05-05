# Open Food Ledger

> Languages: **English** · [Türkçe](README.tr.md)
> Documentation: [English](docs/en/) · [Türkçe](docs/tr/)

A personal calorie, macro, and gram-weight food journal. Log meals from your browser or through an AI assistant, see daily/weekly totals, and track progress toward your goals.

![Demo](assets/Video%20Project.gif)

## What does it do?

Three ways to log what you eat:

- **From the browser** — a simple SPA: create an account, add a meal, see your day
- **From an AI** — write to Claude or ChatGPT in natural language: *"80g oats, breakfast, 320 calories"* — the AI logs, queries, and analyzes for you
- **Export to Excel** — build your own reports, integrate with other apps

Your data lives in your own Postgres. You stay in control.

## Quick start

All you need: Docker.

```bash
git clone <repo-url> open-food-ledger
cd open-food-ledger
docker compose -f compose.dev.yml up --build
```

For a production-like stack (no frontend, source baked in, no reload):
```bash
docker compose -f compose.prod.yml up --build -d
```

The dev stack brings up four containers:

| Container | Port | What it does |
|---|---|---|
| `frontend` | http://localhost:5173 | Vite dev server (Node 20), HMR enabled, proxies `/api/*` to `:8000` |
| `api` | http://localhost:8000 | FastAPI, JSON-only (`/api/*`, `/docs`) |
| `db` | :5432 | PostgreSQL 16 |

Open **http://localhost:5173** in your browser, click **Create account** (password min. 8 characters), and start logging meals. On first launch Postgres takes a second or two to initialize and the tables are created automatically.

> **Note:** the `frontend` container uses a dev-grade Vite dev server (HMR + source bind mount). `compose.prod.yml` does **not** include the frontend service — production deployment (static hosting, CDN, edge cache) is left to your CI/CD or cloud provider (Vercel, Cloudflare Pages, S3 + CloudFront, etc.).

## Connecting to an AI

Two paths:

- **Claude Desktop / Claude Code** — local machine, stdio transport
- **ChatGPT, Claude.ai connectors**, or any other remote client — HTTPS + OAuth

Step-by-step setup for both: **[docs/en/mcp.md](docs/en/mcp.md)** ([Türkçe](docs/tr/mcp.md))

Example prompts once connected:
> *"What did I eat today and how many calories did I have?"*
> *"Add 80g oatmeal, 320 calories, 10g protein as breakfast"*
> *"How does my macro split look this past week, and how am I tracking against my 2200-calorie / 140g-protein goal?"*

## More information

| Document | EN | TR |
|---|---|---|
| MCP server setup (stdio and HTTP), tool list, example configs | [en/mcp.md](docs/en/mcp.md) | [tr/mcp.md](docs/tr/mcp.md) |
| REST API endpoint reference | [en/api.md](docs/en/api.md) | [tr/api.md](docs/tr/api.md) |
| OAuth 2.0 flow, `.well-known` endpoints, PKCE details | [en/oauth.md](docs/en/oauth.md) | [tr/oauth.md](docs/tr/oauth.md) |
| Architecture diagram, data schema, auth model, security notes | [en/architecture.md](docs/en/architecture.md) | [tr/architecture.md](docs/tr/architecture.md) |
| Production deployment guide — HTTPS, secrets, migrations, rate limiting, observability | [en/deployment.md](docs/en/deployment.md) | [tr/deployment.md](docs/tr/deployment.md) |

## Development

`docker compose up` brings everything up, but for faster iteration:

**Backend (without Docker):**
```bash
uv sync                                         # creates .venv, installs from uv.lock
export DATABASE_URL="postgresql+psycopg://openfoodledger:openfoodledger@localhost:5432/openfoodledger"
uv run uvicorn app.main:app --reload
```

`pyproject.toml` + `uv.lock` is the single source of truth — there is no `requirements.txt`. To add a new dependency: `uv add <package>`.

In `compose.dev.yml` the api service runs with build `target: dev` (with `--reload` baked into the Dockerfile) and `./app` is mounted from the host — Python code changes are picked up instantly. `compose.prod.yml` uses `target: prod`: source is baked in, no bind mount, no reload.

**Frontend (Vite hot-reload, Node 18+):**
```bash
cd frontend
npm install
npm run dev   # → http://localhost:5173, /api/* requests proxied to :8000
```

When frontend code changes, rebuild the container: `docker compose up --build frontend`.

**Stack:** FastAPI + SQLAlchemy 2.0 + psycopg + bcrypt + openpyxl, PostgreSQL 16, React + Vite + TypeScript SPA (`frontend/`), `mcp>=1.27.0`. Details in [docs/en/architecture.md](docs/en/architecture.md).

## License

MIT (or your choice).
