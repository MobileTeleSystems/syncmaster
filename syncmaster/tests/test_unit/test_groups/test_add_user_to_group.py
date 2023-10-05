import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_not_authorized_user_cannot_add_user_to_group(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    result = await client.post(f"v1/groups/{empty_group.id}/users/{simple_user.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_not_member_group_cannot_add_user_to_group(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


async def test_member_group_cannot_add_user_to_group(
    client: AsyncClient, not_empty_group: MockGroup, simple_user: MockUser
):
    user = not_empty_group.members[0]
    result = await client.post(
        f"v1/groups/{not_empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_admin_of_group_can_add_user_to_group(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully added to group",
    }

    result = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 1,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": simple_user.id,
                "username": simple_user.username,
                "is_superuser": False,
            }
        ],
    }


async def test_superuser_can_add_user_to_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
    superuser: MockUser,
):
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully added to group",
    }

    result = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 1,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": simple_user.id,
                "username": simple_user.username,
                "is_superuser": False,
            }
        ],
    }


async def test_cannot_add_user_to_group_twice(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully added to group",
    }

    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "User already is group member",
    }


async def test_cannot_add_user_to_incorrect_group(
    client: AsyncClient,
    superuser: MockUser,
    simple_user: MockUser,
):
    result = await client.post(
        f"v1/groups/-1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }
