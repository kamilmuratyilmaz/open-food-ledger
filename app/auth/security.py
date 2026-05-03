"""Pure auth helpers: password hashing and token generation."""
from __future__ import annotations

import secrets

import bcrypt


def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()


def verify_password(pw: str, h: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode(), h.encode())
    except Exception:
        return False


def new_token() -> str:
    return secrets.token_urlsafe(32)
