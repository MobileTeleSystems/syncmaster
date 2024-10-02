import pytest
from httpx import AsyncClient

from tests.mocks import MockUser

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_get_users(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    deleted_user: MockUser,
):
    response = await client.get("v1/users")
    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }

    response = await client.get(
        "v1/users",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 200
    result = response.json()
    assert result.keys() == {"items", "meta"}
    assert result["items"][0].keys() == {"id", "is_superuser", "username"}
    assert result["meta"] == {
        "page": 1,
        "pages": 1,
        "total": len(result["items"]),
        "page_size": 20,
        "has_next": False,
        "has_previous": False,
        "next_page": None,
        "previous_page": None,
    }
    for user_data in result["items"]:
        assert user_data["username"] != deleted_user.username

    response = await client.get(
        "v1/users",
        headers={"Authorization": f"Bearer {inactive_user.token}"},
    )
    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "Inactive user",
            "details": None,
        },
    }


async def test_get_current_user(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
):
    # not authenticated user
    response = await client.get("/v1/users/me")
    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }

    # active user
    response = await client.get(
        "/v1/users/me",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": simple_user.id,
        "is_superuser": simple_user.is_superuser,
        "username": simple_user.username,
    }

    # inactive user
    response = await client.get(
        "/v1/users/me",
        headers={"Authorization": f"Bearer {inactive_user.token}"},
    )
    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "Inactive user",
            "details": None,
        },
    }


async def test_get_user(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    deleted_user: MockUser,
):
    response = await client.get(f"/v1/users/{simple_user.id}")
    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }

    # check from simple user
    response = await client.get(
        f"v1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": simple_user.id,
        "is_superuser": simple_user.is_superuser,
        "username": simple_user.username,
    }

    # check from simple user deleted user
    response = await client.get(
        f"v1/users/{deleted_user.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }

    # check from inactive user
    response = await client.get(
        f"v1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {inactive_user.token}"},
    )
    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "Inactive user",
            "details": None,
        },
    }
