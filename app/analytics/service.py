"""Aggregation helpers shared by analytics routes."""
from __future__ import annotations

from typing import Iterable

from app.db.models import FoodEntry

NUMERIC_KEYS = [
    "calories", "protein_g", "carbs_g", "fat_g",
    "fiber_g", "sugar_g", "sodium_mg", "weight_g",
]


def aggregate(entries: Iterable[FoodEntry]) -> dict[str, float]:
    """Sum the standard nutrient columns across `entries`, rounded to 2 decimals."""
    rows = list(entries)
    return {k: round(sum(getattr(e, k) for e in rows), 2) for k in NUMERIC_KEYS}
