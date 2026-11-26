"""Async database engine and session factory (SQLAlchemy 2.x + asyncpg).

The engine is created lazily on first use, so importing the app never needs a
database or configuration (useful for tooling, linting and tests).
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from functools import lru_cache

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Declarative base for ORM models. Alembic autogenerate reads ``Base.metadata``."""


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    url = get_settings().database_url.get_secret_value()
    return create_async_engine(
        url,
        pool_pre_ping=True,
        hide_parameters=True,  # keep bound values out of error messages and logs
        connect_args={"timeout": 5},  # asyncpg connect timeout, seconds
    )


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(get_engine(), expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI dependency yielding a session that is closed after the request."""
    async with get_sessionmaker()() as session:
        yield session


async def dispose_engine() -> None:
    """Close pooled connections and forget the engine (app shutdown / tests)."""
    if get_engine.cache_info().currsize:
        await get_engine().dispose()
    get_sessionmaker.cache_clear()
    get_engine.cache_clear()
