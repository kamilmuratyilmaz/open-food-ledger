"""Food-entry CRUD routes: /api/entries*."""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.db.models import FoodEntry, User
from app.db.session import get_db
from app.entries.schemas import EntryIn, EntryOut, EntryUpdate
from app.entries.service import entry_to_dict, normalize_meal_type

router = APIRouter(prefix="/api/entries", tags=["entries"])


@router.post("", response_model=EntryOut)
def create_entry(payload: EntryIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    e = FoodEntry(
        user_id=user.id,
        entry_date=payload.entry_date or date.today(),
        entry_time=payload.entry_time or datetime.now().strftime("%H:%M"),
        meal_type=normalize_meal_type(payload.meal_type),
        food_name=payload.food_name,
        weight_g=payload.weight_g,
        calories=payload.calories, protein_g=payload.protein_g,
        carbs_g=payload.carbs_g, fat_g=payload.fat_g,
        fiber_g=payload.fiber_g, sugar_g=payload.sugar_g,
        sodium_mg=payload.sodium_mg, notes=payload.notes,
    )
    db.add(e)
    db.commit()
    db.refresh(e)
    return entry_to_dict(e)


@router.get("", response_model=list[EntryOut])
def list_entries(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    meal_type: Optional[str] = None,
    food_query: Optional[str] = None,
    limit: int = Query(default=200, ge=1, le=2000),
):
    stmt = select(FoodEntry).where(FoodEntry.user_id == user.id)
    if start_date:
        stmt = stmt.where(FoodEntry.entry_date >= start_date)
    if end_date:
        stmt = stmt.where(FoodEntry.entry_date <= end_date)
    if meal_type:
        stmt = stmt.where(FoodEntry.meal_type == meal_type.lower())
    if food_query:
        stmt = stmt.where(FoodEntry.food_name.ilike(f"%{food_query}%"))
    stmt = stmt.order_by(FoodEntry.entry_date.desc(), FoodEntry.entry_time.desc()).limit(limit)
    return [entry_to_dict(e) for e in db.scalars(stmt)]


@router.patch("/{entry_id}", response_model=EntryOut)
def update_entry(
    entry_id: uuid.UUID, payload: EntryUpdate,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    e = db.scalar(select(FoodEntry).where(FoodEntry.id == entry_id, FoodEntry.user_id == user.id))
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    data = payload.model_dump(exclude_unset=True)
    if "meal_type" in data:
        data["meal_type"] = normalize_meal_type(data["meal_type"])
    for k, v in data.items():
        setattr(e, k, v)
    db.commit()
    db.refresh(e)
    return entry_to_dict(e)


@router.delete("/{entry_id}")
def delete_entry(
    entry_id: uuid.UUID,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    e = db.scalar(select(FoodEntry).where(FoodEntry.id == entry_id, FoodEntry.user_id == user.id))
    if not e:
        raise HTTPException(status_code=404, detail="Entry not found")
    db.delete(e)
    db.commit()
    return {"ok": True, "deleted_id": str(entry_id)}
