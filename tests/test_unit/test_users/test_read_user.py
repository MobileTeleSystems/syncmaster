import pytest
from httpx import AsyncClient

from tests.mocks import MockUser

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_get_user_unauthorized(client: AsyncClient):
    response = await client.get("/v1/users/some_user_id")
    assert response.status_code == 401, response.json()
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_get_user_authorized(client: AsyncClient, simple_user: MockUser):
    response = await client.get(
        f"/v1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "id": simple_user.id,
        "is_superuser": simple_user.is_superuser,
        "username": simple_user.username,
    }


async def test_get_user_inactive(client: AsyncClient, simple_user: MockUser, inactive_user: MockUser):
    response = await client.get(
        f"/v1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {inactive_user.token}"},
    )
    assert response.status_code == 403, response.json()
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_get_current_user_unauthorized(client: AsyncClient):
    response = await client.get("/v1/users/me")
    assert response.status_code == 401, response.json()
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_get_current_user_authorized(client: AsyncClient, simple_user: MockUser):
    response = await client.get(
        "/v1/users/me",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "id": simple_user.id,
        "is_superuser": simple_user.is_superuser,
        "username": simple_user.username,
    }


async def test_get_current_user_inactive(client: AsyncClient, inactive_user: MockUser):
    response = await client.get(
        "/v1/users/me",
        headers={"Authorization": f"Bearer {inactive_user.token}"},
    )
    assert response.status_code == 403, response.json()
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
