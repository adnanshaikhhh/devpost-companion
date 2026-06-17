"""
SQLAlchemy engine, session factory, and declarative base.

A single SQLite file is used for simplicity. The session is yielded
per-request via the `get_db` dependency.
"""
from __future__ import annotations

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# `check_same_thread=False` is the SQLite-specific tweak we need when
# sharing the connection across FastAPI's thread pool.
connect_args = (
    {"check_same_thread": False}
    if settings.database_url.startswith("sqlite")
    else {}
)

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    future=True,
)


class Base(DeclarativeBase):
    """Declarative base used by all ORM models."""


def init_db() -> None:
    """Create all tables. Idempotent — safe to call on every boot."""
    # Importing models registers them with the metadata
    from models import Project  # noqa: F401

    Base.metadata.create_all(bind=engine)
    logger.info("Database initialised (%d tables)", len(Base.metadata.tables))


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a transactional session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()