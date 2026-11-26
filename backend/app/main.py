"""FastAPI application entry point. Run with: ``uvicorn app.main:app --reload``."""

from __future__ import annotations

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, status
from sqlalchemy import text

from app.api.v1 import api_router
from app.core.db import dispose_engine, get_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    yield
    await dispose_engine()


app = FastAPI(title="QA Studio API", version="0.1.0", lifespan=lifespan)
app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["health"])
async def health(response: Response) -> dict[str, str]:
    """Liveness plus a database round-trip. Returns 503 if the database is unreachable."""
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
    except Exception:
        # Log the exception type only: driver messages can include connection details.
        logger.warning("Health check failed: database unavailable", exc_info=False)
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "degraded", "database": "unavailable"}
    return {"status": "ok", "database": "ok"}
