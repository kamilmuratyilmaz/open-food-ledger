"""Auth and user-profile routes: /api/auth/* and /api/me*."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthIn, AuthOut, UserOut
from app.auth.security import hash_password, new_token, verify_password
from app.db.models import User
from app.db.session import get_db

router = APIRouter(prefix="/api", tags=["auth"])


@router.post("/auth/register", response_model=AuthOut)
def register(payload: AuthIn, db: Session = Depends(get_db)):
    existing = db.scalar(select(User).where(User.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=payload.email.lower(),
        password_hash=hash_password(payload.password),
        api_token=new_token(),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return AuthOut(user_id=user.id, email=user.email, api_token=user.api_token)


@router.post("/auth/login", response_model=AuthOut)
def login(payload: AuthIn, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == payload.email.lower()))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return AuthOut(user_id=user.id, email=user.email, api_token=user.api_token)


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return UserOut(
        user_id=user.id, email=user.email,
        api_token=user.api_token, created_at=user.created_at,
    )


@router.post("/me/rotate-token", response_model=AuthOut)
def rotate_token(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.api_token = new_token()
    db.commit()
    return AuthOut(user_id=user.id, email=user.email, api_token=user.api_token)
