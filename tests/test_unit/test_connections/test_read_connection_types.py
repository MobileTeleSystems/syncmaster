import pytest
from httpx import AsyncClient

from syncmaster.schemas.v1.connection_types import CONNECTION_TYPES
from tests.mocks import MockUser

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_unauthorized_user_cannot_read_connection_types(client: AsyncClient):
    result = await client.get("v1/connections/known_types")
    assert result.status_code == 401, result.json()
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_groupless_user_can_read_connection_types(client: AsyncClient, simple_user: MockUser):
    result = await client.get(
        "v1/connections/known_types",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 200, result.json()
    assert set(result.json()) == set(CONNECTION_TYPES)
