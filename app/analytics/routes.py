"""Analytics routes: /api/analytics/*."""
from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.analytics.service import aggregate
from app.auth.dependencies import get_current_user
from app.config import MEAL_TYPES
from app.db.models import FoodEntry, User
from app.db.session import get_db
from app.entries.service import entry_to_dict

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/daily")
def daily_totals(
    target_date: Optional[date] = None,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    d = target_date or date.today()
    rows = list(db.scalars(
        select(FoodEntry).where(FoodEntry.user_id == user.id, FoodEntry.entry_date == d)
    ))
    by_meal: dict[str, list] = {m: [] for m in MEAL_TYPES}
    for e in rows:
        by_meal.setdefault(e.meal_type, []).append(e)
    return {
        "date": d.isoformat(),
        "entry_count": len(rows),
        "totals": aggregate(rows),
        "by_meal": {m: aggregate(es) for m, es in by_meal.items()},
    }


@router.get("/range")
def range_summary(
    start_date: date, end_date: date,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    rows = list(db.scalars(
        select(FoodEntry).where(
            FoodEntry.user_id == user.id,
            FoodEntry.entry_date >= start_date,
            FoodEntry.entry_date <= end_date,
        )
    ))
    by_day: dict[str, list] = {}
    for e in rows:
        by_day.setdefault(e.entry_date.isoformat(), []).append(e)
    daily = {d: aggregate(es) for d, es in sorted(by_day.items())}
    n_days = (end_date - start_date).days + 1
    overall = aggregate(rows)
    avg = {k: round(v / n_days, 2) for k, v in overall.items()} if n_days else overall
    return {
        "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
        "days_in_range": n_days, "days_with_entries": len(by_day),
        "overall_totals": overall, "daily_averages": avg, "per_day": daily,
    }


@router.get("/macros")
def analyze_macros(
    start_date: date, end_date: date,
    target_calories: Optional[float] = None,
    target_protein_g: Optional[float] = None,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    rows = list(db.scalars(
        select(FoodEntry).where(
            FoodEntry.user_id == user.id,
            FoodEntry.entry_date >= start_date,
            FoodEntry.entry_date <= end_date,
        )
    ))
    if not rows:
        return {"start_date": start_date.isoformat(), "end_date": end_date.isoformat(), "entry_count": 0}
    by_day: dict[str, list] = {}
    for e in rows:
        by_day.setdefault(e.entry_date.isoformat(), []).append(e)
    total = aggregate(rows)
    pK, cK, fK = total["protein_g"] * 4, total["carbs_g"] * 4, total["fat_g"] * 9
    den = (pK + cK + fK) or 1
    dist = {
        "protein_pct": round(pK / den * 100, 1),
        "carbs_pct":   round(cK / den * 100, 1),
        "fat_pct":     round(fK / den * 100, 1),
    }
    out: dict = {
        "start_date": start_date.isoformat(), "end_date": end_date.isoformat(),
        "entry_count": len(rows), "totals": total, "macro_distribution_pct": dist,
    }
    if target_calories or target_protein_g:
        days = []
        for d, es in sorted(by_day.items()):
            dt = aggregate(es)
            row = {"date": d, **dt}
            if target_calories:
                row["calories_pct_of_target"] = round(dt["calories"] / target_calories * 100, 1)
            if target_protein_g:
                row["protein_pct_of_target"] = round(dt["protein_g"] / target_protein_g * 100, 1)
            days.append(row)
        out["target_adherence"] = {
            "target_calories": target_calories,
            "target_protein_g": target_protein_g,
            "days": days,
        }
    return out


@router.get("/find")
def find_food(
    q: str, limit: int = Query(20, ge=1, le=200),
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    rows = list(db.scalars(
        select(FoodEntry)
        .where(FoodEntry.user_id == user.id, FoodEntry.food_name.ilike(f"%{q}%"))
        .order_by(FoodEntry.entry_date.desc(), FoodEntry.entry_time.desc())
        .limit(limit)
    ))
    return {"query": q, "count": len(rows), "matches": [entry_to_dict(e) for e in rows]}


@router.get("/suggest")
def suggest_meal(
    meal_type: str,
    user: User = Depends(get_current_user), db: Session = Depends(get_db),
):
    meal = meal_type.lower()
    if meal not in MEAL_TYPES:
        raise HTTPException(status_code=422, detail="bad meal_type")
    cutoff = date.today() - timedelta(days=30)
    rows = list(db.scalars(
        select(FoodEntry).where(
            FoodEntry.user_id == user.id,
            FoodEntry.meal_type == meal,
            FoodEntry.entry_date >= cutoff,
        )
    ))
    counts: dict[str, dict] = {}
    for e in rows:
        c = counts.setdefault(e.food_name, {
            "food_name": e.food_name, "times_eaten": 0,
            "_w": 0.0, "_c": 0.0,
        })
        c["times_eaten"] += 1
        c["_w"] += e.weight_g
        c["_c"] += e.calories
    arr = [
        {
            "food_name": c["food_name"],
            "times_eaten": c["times_eaten"],
            "avg_weight_g": round(c["_w"] / c["times_eaten"], 1),
            "avg_calories": round(c["_c"] / c["times_eaten"], 1),
        }
        for c in counts.values()
    ]
    arr.sort(key=lambda x: -x["times_eaten"])
    return {"meal_type": meal, "window_days": 30, "frequent_foods": arr[:10]}
