import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_ping_route(client: AsyncClient):
    response = await client.get("/monitoring/ping")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
