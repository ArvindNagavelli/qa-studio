"""Shared test fixtures.

PostgreSQL comes from ``pixeltable-pgserver``: real PostgreSQL 16 binaries shipped in a
pip wheel, started in a temp directory. No Docker and no system packages needed.
"""

from __future__ import annotations

import shutil
import tempfile
import time
import uuid
import warnings
from collections.abc import AsyncIterator, Iterator
from pathlib import Path

import httpx
import pytest
from pixeltable_pgserver.postgres_server import get_server

PG_DIR_PREFIX = "qa-studio-pg-"

# Test-only, non-secret values. Applied per fixture, never written to disk.
TEST_ENV = {
    "APP_ENV": "test",
    "JWT_SECRET": "test-only-signing-key-not-a-real-secret-0000",  # pragma: allowlist secret
    "LLM_PROVIDER": "mock",
    "DEV_LOGIN": "false",
}


def _remove_dir(path: Path, attempts: int = 10, delay: float = 0.5) -> None:
    """Delete ``path``, retrying briefly: on Windows a just-stopped PostgreSQL can keep
    file handles open for a moment. Warn (never silently leak) if it still fails."""
    for _ in range(attempts):
        shutil.rmtree(path, ignore_errors=True)
        if not path.exists():
            return
        time.sleep(delay)
    warnings.warn(f"could not delete temporary database folder {path}", stacklevel=2)


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    """Start a throwaway embedded PostgreSQL for the test session.

    The data lives in a fresh folder in the system temp directory, NOT in pytest's
    ``tmp_path``: on Windows with Python 3.12.4+, pytest's temp folders get an owner-only
    ACL, and when tests run as Administrator (as on GitHub's Windows runners) PostgreSQL
    drops its admin rights before ``initdb`` and can no longer open such a folder. A folder
    created with default permissions inherits the temp directory's ACL and works.

    The folder is always removed at the end of the session, also when PostgreSQL fails
    to start or a test fails.
    """
    base = Path(tempfile.gettempdir()) / f"{PG_DIR_PREFIX}{uuid.uuid4().hex[:12]}"
    base.mkdir()  # default mode on purpose: see docstring (tempfile.mkdtemp uses 0o700)
    try:
        server = get_server(base / "pgdata", cleanup_mode="delete")
        try:
            yield server.get_uri(driver="asyncpg")
        finally:
            server.cleanup()
    finally:
        _remove_dir(base)


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
