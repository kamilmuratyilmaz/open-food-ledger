"""FastAPI dependency that extracts the current user from a Bearer token."""
from __future__ import annotations

from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import User
from app.db.session import get_db


def get_current_user(
    authorization: Annotated[Optional[str], Header()] = None,
    db: Session = Depends(get_db),
) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization[7:].strip()
    user = db.scalar(select(User).where(User.api_token == token))
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user
