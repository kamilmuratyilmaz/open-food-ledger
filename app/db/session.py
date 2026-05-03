"""SQLAlchemy engine, declarative Base, and request-scoped DB session dependency."""
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session

from app.config import DATABASE_URL

engine = create_engine(DATABASE_URL, pool_pre_ping=True, echo=False)


class Base(DeclarativeBase):
    pass


def get_db():
    with Session(engine) as session:
        yield session
