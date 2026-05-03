"""Pydantic schemas for food entries."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class EntryIn(BaseModel):
    food_name: str = Field(min_length=1, max_length=255)
    weight_g: float = Field(ge=0)
    meal_type: str
    calories: float = 0
    protein_g: float = 0
    carbs_g: float = 0
    fat_g: float = 0
    fiber_g: float = 0
    sugar_g: float = 0
    sodium_mg: float = 0
    notes: Optional[str] = None
    entry_date: Optional[date] = None
    entry_time: Optional[str] = None


class EntryUpdate(BaseModel):
    food_name: Optional[str] = None
    weight_g: Optional[float] = None
    meal_type: Optional[str] = None
    calories: Optional[float] = None
    protein_g: Optional[float] = None
    carbs_g: Optional[float] = None
    fat_g: Optional[float] = None
    fiber_g: Optional[float] = None
    sugar_g: Optional[float] = None
    sodium_mg: Optional[float] = None
    notes: Optional[str] = None
    entry_date: Optional[date] = None
    entry_time: Optional[str] = None


class EntryOut(BaseModel):
    id: uuid.UUID
    entry_date: date
    entry_time: Optional[str]
    meal_type: str
    food_name: str
    weight_g: float
    calories: float
    protein_g: float
    carbs_g: float
    fat_g: float
    fiber_g: float
    sugar_g: float
    sodium_mg: float
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
