"""ORM models. Importing this module registers tables on Base.metadata."""
from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import Date, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    api_token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    entries: Mapped[list["FoodEntry"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class FoodEntry(Base):
    __tablename__ = "food_entries"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    entry_time: Mapped[Optional[str]] = mapped_column(String(5), nullable=True)
    meal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    food_name: Mapped[str] = mapped_column(String(255), nullable=False)
    weight_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    calories: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    protein_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    carbs_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    fat_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    fiber_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    sugar_g: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    sodium_mg: Mapped[float] = mapped_column(Float, nullable=False, default=0)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    user: Mapped[User] = relationship(back_populates="entries")
