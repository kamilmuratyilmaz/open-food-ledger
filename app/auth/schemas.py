"""Pydantic schemas for the auth domain."""
from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AuthIn(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class AuthOut(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    api_token: str


class UserOut(BaseModel):
    user_id: uuid.UUID
    email: EmailStr
    api_token: str
    created_at: datetime
