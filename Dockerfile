# ---- Stage 1: install Python dependencies with uv ----
FROM python:3.13-slim AS builder

# Pull the uv binary from Astral's official distribution image.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /app

# UV_LINK_MODE=copy: don't rely on hardlinks (cross-volume safe).
# UV_COMPILE_BYTECODE=1: precompile .pyc for faster cold start.
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1

# Install dependencies first so changes to app/ don't bust this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Copy the application package + alembic config.
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations

# ---- Common runtime base (shared by dev and prod) ----
FROM python:3.13-slim AS base
WORKDIR /app

# psycopg needs libpq's runtime library.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user. uvicorn workers and (in dev) the reloader run as this user.
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --no-create-home --shell /usr/sbin/nologin app

# Bring in the populated venv from the builder, owned by the unprivileged user.
COPY --from=builder --chown=app:app /app/.venv /app/.venv

# Put the venv's executables on PATH so `uvicorn` and `alembic` resolve directly.
ENV PATH="/app/.venv/bin:$PATH"

# ---- Dev runtime: source baked AND --reload enabled ----
# The dev compose file overlays /app/app, /app/migrations, and /app/alembic.ini
# with bind mounts; uvicorn --reload watches them. The bake-in still lets
# `docker run --rm <image>:dev` work standalone without a bind mount.
FROM base AS dev
COPY --from=builder --chown=app:app /app/app /app/app
COPY --from=builder --chown=app:app /app/alembic.ini /app/alembic.ini
COPY --from=builder --chown=app:app /app/migrations /app/migrations
USER app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"]

# ---- Prod runtime: source baked, NO --reload ----
# Identical layer set to `dev` except for the CMD; the file system watcher is
# disabled (perf + read-only filesystem friendliness).
FROM base AS prod
COPY --from=builder --chown=app:app /app/app /app/app
COPY --from=builder --chown=app:app /app/alembic.ini /app/alembic.ini
COPY --from=builder --chown=app:app /app/migrations /app/migrations
USER app
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
