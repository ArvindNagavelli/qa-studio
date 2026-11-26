from __future__ import annotations

import httpx


async def test_health_ok_with_database(client: httpx.AsyncClient) -> None:
    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


async def test_health_reports_unavailable_database(client_without_db: httpx.AsyncClient) -> None:
    response = await client_without_db.get("/health")

    assert response.status_code == 503
    assert response.json() == {"status": "degraded", "database": "unavailable"}
