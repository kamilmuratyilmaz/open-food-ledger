"""FastAPI app assembly: middleware + routers.

Schema is managed by Alembic. Migrations are applied as a separate
step before the app starts (see docker-compose.yml's api command and
docs/*/deployment.md), not from inside the application.
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analytics.routes import router as analytics_router
from app.auth.routes import router as auth_router
from app.config import ALLOWED_ORIGINS
from app.entries.routes import router as entries_router
from app.export.routes import router as export_router


app = FastAPI(title="Open Food Ledger", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(entries_router)
app.include_router(analytics_router)
app.include_router(export_router)
