import pytest
from httpx import AsyncClient
from tests.utils import MockUser

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_read_connection_types(client: AsyncClient):
    result = await client.get("v1/connections/known_types")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_simple_user_read_connection_types(
    client: AsyncClient, simple_user: MockUser
):
    result = await client.get(
        "v1/connections/known_types",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 200
    assert set(result.json()) == {"postgres", "oracle"}
