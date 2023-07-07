import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_ping_route(async_client: AsyncClient):
    response = await async_client.get("/monitoring/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
