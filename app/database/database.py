"""
Database engine and session factory.

The SQLAlchemy ``Engine`` is created lazily via ``_get_engine()`` which is
decorated with ``@lru_cache(maxsize=1)``.  This means the engine (and its
underlying connection pool) is **not** instantiated at import time, saving
memory on startup.  The first call to ``SessionLocal()`` or
``_get_engine()`` triggers engine creation.
"""

from __future__ import annotations

from functools import lru_cache

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings


@lru_cache(maxsize=1)
def _get_engine():
    """Return the singleton SQLAlchemy Engine, created on first call."""
    return create_engine(
        settings.database_url,
        connect_args={"check_same_thread": False},
    )


def _make_session_factory():
    """Return a sessionmaker bound to the lazy engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=_get_engine())


class _LazySessionLocal:
    """Drop-in replacement for a ``sessionmaker`` instance.

    Calling ``SessionLocal()`` triggers engine creation on first use.  This
    keeps the SQLAlchemy engine out of the import graph while preserving the
    same call interface that the rest of the codebase (and tests) rely on.
    """

    def __call__(self) -> Session:
        return _make_session_factory()()

    def __enter__(self):  # allows `with SessionLocal() as db:` pattern
        self._session = _make_session_factory()()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._session.close()


SessionLocal = _LazySessionLocal()

Base = declarative_base()


def get_engine():
    """Public accessor used by ``main.py`` startup event."""
    return _get_engine()
