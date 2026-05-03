"""Helpers shared by entry routes: serialization and meal_type validation."""
from __future__ import annotations

from fastapi import HTTPException

from app.config import MEAL_TYPES
from app.db.models import FoodEntry


def entry_to_dict(e: FoodEntry) -> dict:
    return {
        "id": e.id, "entry_date": e.entry_date, "entry_time": e.entry_time,
        "meal_type": e.meal_type, "food_name": e.food_name,
        "weight_g": e.weight_g, "calories": e.calories,
        "protein_g": e.protein_g, "carbs_g": e.carbs_g, "fat_g": e.fat_g,
        "fiber_g": e.fiber_g, "sugar_g": e.sugar_g, "sodium_mg": e.sodium_mg,
        "notes": e.notes, "created_at": e.created_at,
    }


def normalize_meal_type(value: str) -> str:
    """Lower-case `value` and assert it's a known meal type. Raises 422 otherwise."""
    normalized = value.lower()
    if normalized not in MEAL_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"meal_type must be one of {sorted(MEAL_TYPES)}",
        )
    return normalized
