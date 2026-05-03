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

# Copy the application package. We don't `uv sync` again because we use
# --no-install-project (the project itself isn't a library to install;
# `app/` is just imported from cwd at runtime).
COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations

# ---- Stage 2: minimal runtime ----
FROM python:3.13-slim
WORKDIR /app

# psycopg needs libpq's runtime library.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Non-root user. uvicorn workers and reloader run as this user.
RUN groupadd --system --gid 1000 app \
    && useradd --system --uid 1000 --gid app --no-create-home --shell /usr/sbin/nologin app

# Copy venv + source from builder, owned by the unprivileged user.
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/app /app/app
COPY --from=builder --chown=app:app /app/alembic.ini /app/alembic.ini
COPY --from=builder --chown=app:app /app/migrations /app/migrations

# Put the venv's executables on PATH so `uvicorn` resolves without `uv run`.
ENV PATH="/app/.venv/bin:$PATH"

USER app

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
