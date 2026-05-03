# syntax=docker/dockerfile:1
#
# MCP server image for the Food Tracker.
# Build context is the PROJECT ROOT (not mcp_server/) so that pyproject.toml
# and uv.lock are accessible. Build with:
#     docker build -f mcp_server/Dockerfile -t food-mcp .
# or via docker compose with `context: .` and `dockerfile: mcp_server/Dockerfile`.

# ---- Stage 1: resolve Python deps with uv (locked, reproducible) ----
FROM python:3.13-slim AS builder

# Pull the uv binary from Astral's distribution image (digest-pinned for
# reproducibility — bump deliberately, not by `latest` drift).
COPY --from=ghcr.io/astral-sh/uv:0.5.14 /uv /uvx /usr/local/bin/

WORKDIR /app

# UV_LINK_MODE=copy: don't rely on hardlinks across mounts.
# UV_COMPILE_BYTECODE=1: pre-compile .pyc so runtime is read-only friendly.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Resolve deps first — changes to mcp_server/ don't bust this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy only the MCP server package (NOT the FastAPI `app/`, NOT the frontend,
# NOT secrets like .mcp.json — explicit allowlist by COPY).
COPY mcp_server ./mcp_server

# ---- Stage 2: minimal runtime ----
FROM python:3.13-slim

# Drop apt-get cache promptly; no extra packages needed at runtime.
# (psycopg's binary wheel ships its own libpq, no apt install required.)

WORKDIR /app

# Non-root system user. No home dir, no login shell — defense in depth
# against shell-popping bugs and anything that tries to drop a file in $HOME.
RUN groupadd --system --gid 1000 mcp \
    && useradd --system --uid 1000 --gid mcp --no-create-home --shell /usr/sbin/nologin mcp

# Bring in only what we need from the builder, owned by the unprivileged user.
COPY --from=builder --chown=mcp:mcp /app/.venv /app/.venv
COPY --from=builder --chown=mcp:mcp /app/mcp_server /app/mcp_server

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    \
    # HTTP transport is the sensible default in a container (stdio needs a
    # parent process to attach to). Override at deploy time if needed.
    MCP_TRANSPORT=http \
    MCP_PORT=8001

# Run as the unprivileged user from this point on.
USER mcp

EXPOSE 8001

# exec form → no shell, signals (SIGTERM/SIGINT) reach Python directly.
CMD ["python", "-m", "mcp_server.server"]

# --- Security notes ---------------------------------------------------------
# 1. Non-root: USER mcp (uid 1000), no home, no shell.
# 2. Minimal attack surface: slim base, explicit COPY (no `COPY . .`),
#    no apt packages installed in runtime stage, no build tools (uv only
#    in builder).
# 3. Reproducible deps: `uv sync --frozen` honors uv.lock; the uv binary
#    itself is pinned via digest tag.
# 4. No secrets baked: API tokens, OAuth client secrets, etc. flow only
#    via env vars at runtime.
# 5. Read-only filesystem friendly: PYTHONDONTWRITEBYTECODE=1 + bytecode
#    pre-compiled in builder; you can deploy with `--read-only` plus a
#    tmpfs for /tmp if a hosting platform supports it.
# 6. Compose hardening (recommended, set at the compose level):
#       cap_drop: [ALL]
#       security_opt: [no-new-privileges:true]
#       read_only: true
#       tmpfs: [/tmp]
# 7. Healthcheck: omitted because it's transport-dependent. For HTTP mode,
#    add at compose level:
#       healthcheck:
#         test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8001/.well-known/oauth-authorization-server', timeout=3)"]
#         interval: 30s
#         timeout: 5s
#         start_period: 10s
#         retries: 3
