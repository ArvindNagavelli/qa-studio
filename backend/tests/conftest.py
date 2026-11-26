"""Shared test fixtures.

PostgreSQL comes from ``pixeltable-pgserver``: real PostgreSQL 16 binaries shipped in a
pip wheel, started in a temp directory. No Docker and no system packages needed.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator

import httpx
import pytest
from pixeltable_pgserver.postgres_server import get_server

# Test-only, non-secret values. Applied per fixture, never written to disk.
TEST_ENV = {
    "APP_ENV": "test",
    "JWT_SECRET": "test-only-signing-key-not-a-real-secret-0000",  # pragma: allowlist secret
    "LLM_PROVIDER": "mock",
    "DEV_LOGIN": "false",
}


@pytest.fixture(scope="session")
def postgres_url(tmp_path_factory: pytest.TempPathFactory) -> Iterator[str]:
    """Start a throwaway embedded PostgreSQL for the test session."""
    server = get_server(tmp_path_factory.mktemp("pgdata"), cleanup_mode="delete")
    try:
        yield server.get_uri(driver="asyncpg")
    finally:
        server.cleanup()


async def _make_client(database_url: str) -> AsyncIterator[httpx.AsyncClient]:
    from app.core.config import get_settings
    from app.core.db import dispose_engine
    from app.main import app

    with pytest.MonkeyPatch.context() as mp:
        for key, value in {**TEST_ENV, "DATABASE_URL": database_url}.items():
            mp.setenv(key, value)
        get_settings.cache_clear()
        await dispose_engine()
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as client:
            yield client
        await dispose_engine()
        get_settings.cache_clear()


@pytest.fixture
async def client(postgres_url: str) -> AsyncIterator[httpx.AsyncClient]:
    """HTTP client for the app, wired to the embedded database."""
    async for c in _make_client(postgres_url):
        yield c


@pytest.fixture
async def client_without_db() -> AsyncIterator[httpx.AsyncClient]:
    """HTTP client whose DATABASE_URL points at a closed local port."""
    async for c in _make_client("postgresql+asyncpg://nobody@127.0.0.1:1/none"):
        yield c
