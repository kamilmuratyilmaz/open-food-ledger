"""FastAPI app assembly: lifespan, middleware, routers.

Frontend is served by a separate nginx container (see frontend/), which
proxies /api/* here. CORS allow_origins covers cross-container calls
when the frontend container hits this API directly during dev.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.analytics.routes import router as analytics_router
from app.auth.routes import router as auth_router
from app.config import ALLOWED_ORIGINS
from app.db import models  # noqa: F401  -- registers tables on Base.metadata
from app.db.session import Base, engine
from app.entries.routes import router as entries_router
from app.export.routes import router as export_router


@asynccontextmanager
async def lifespan(_app: FastAPI):
    Base.metadata.create_all(engine)
    yield


app = FastAPI(title="Food Tracker", version="1.0", lifespan=lifespan)

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
