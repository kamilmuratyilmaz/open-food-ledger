"""Application-wide constants and environment-derived settings."""
from __future__ import annotations

import os

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql+psycopg://foodtracker:foodtracker@localhost:5432/foodtracker",
)
ALLOWED_ORIGINS = os.environ.get("ALLOWED_ORIGINS", "*").split(",")
MEAL_TYPES: frozenset[str] = frozenset({"breakfast", "lunch", "dinner", "snack"})
