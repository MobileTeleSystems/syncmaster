import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.utils import MockUser


@pytest.mark.asyncio
async def test_get_users(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    deleted_user: MockUser,
):
    response = await client.get("v1/users")
    assert response.status_code == 401
    assert response.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
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
        "ok": False,
        "status_code": response.status_code,
        "message": "Inactive user",
    }


@pytest.mark.asyncio
async def test_get_user(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    deleted_user: MockUser,
):
    response = await client.get(f"/v1/users/{simple_user.id}")
    assert response.status_code == 401
    assert response.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
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
        "ok": False,
        "status_code": 404,
        "message": "User not found",
    }

    # check from inactive user
    response = await client.get(
        f"v1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {inactive_user.token}"},
    )
    assert response.status_code == 403
    assert response.json() == {
        "ok": False,
        "status_code": response.status_code,
        "message": "Inactive user",
    }


@pytest.mark.asyncio
async def test_post_user(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    deleted_user: MockUser,
    superuser: MockUser,
):
    # not auth
    response = await client.post(
        f"v1/users/{simple_user.id}",
        json={"username": "new_username"},
    )
    assert response.status_code == 401
    assert response.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }

    # check correct update
    response = await client.post(
        f"v1/users/{simple_user.id}",
        json={"username": "new_username"},
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": simple_user.id,
        "username": "new_username",
        "is_superuser": simple_user.is_superuser,
    }

    # check incorrect username
    response = await client.post(
        f"v1/users/{simple_user.id}",
        json={"username": "new            username"},
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "loc": ["body", "username"],
                "msg": "Invalid username",
                "type": "value_error",
            }
        ]
    }

    # check change other user from simple
    response = await client.post(
        f"v1/users/{inactive_user.id}",
        json={"username": "username"},
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 403
    assert response.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You cannot change other user",
    }

    # check change other user from superuser
    response = await client.post(
        f"v1/users/{inactive_user.id}",
        json={"username": "username"},
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "id": inactive_user.id,
        "username": "username",
        "is_superuser": False,
    }

    # check change deleted user form superuser
    response = await client.post(
        f"v1/users/{deleted_user.id}",
        json={"username": "username"},
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "ok": False,
        "status_code": 404,
        "message": "User not found",
    }


@pytest.mark.asyncio
async def test_activate_user(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    superuser: MockUser,
    deleted_user: MockUser,
    session: AsyncSession,
):
    # check not auth
    response = await client.post(f"v1/users/{inactive_user.id}/activate")
    assert response.status_code == 401
    assert response.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }

    # check simple user
    response = await client.post(
        f"v1/users/{inactive_user.id}/activate",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 403
    assert response.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }

    # check superuser
    response = await client.post(
        f"v1/users/{inactive_user.id}/activate",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was activated",
    }

    await session.refresh(inactive_user.user)
    assert inactive_user.is_active

    # check activate activated user
    response = await client.post(
        f"v1/users/{simple_user.id}/activate",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was activated",
    }

    await session.refresh(simple_user.user)
    assert simple_user.is_active

    # check activate deleted user
    response = await client.post(
        f"v1/users/{deleted_user.id}/activate",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "ok": False,
        "status_code": 404,
        "message": "User not found",
    }


@pytest.mark.asyncio
async def test_deactivate_user(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    deleted_user: MockUser,
    superuser: MockUser,
    session: AsyncSession,
):
    # check no auth
    response = await client.post(f"v1/users/{simple_user.id}/deactivate")
    assert response.status_code == 401
    assert response.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }

    # check simple user
    response = await client.post(
        f"v1/users/{simple_user.id}/deactivate",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 403
    assert response.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }

    # check superuser
    response = await client.post(
        f"v1/users/{simple_user.id}/deactivate",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was deactivated",
    }

    await session.refresh(simple_user.user)
    assert not simple_user.is_active

    # check deactivate inactive user
    response = await client.post(
        f"v1/users/{inactive_user.id}/deactivate",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 200
    assert response.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was deactivated",
    }

    await session.refresh(inactive_user.user)
    assert not inactive_user.is_active

    # check deactivate deleted user
    response = await client.post(
        f"v1/users/{deleted_user.id}/deactivate",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 404
    assert response.json() == {
        "ok": False,
        "status_code": 404,
        "message": "User not found",
    }
