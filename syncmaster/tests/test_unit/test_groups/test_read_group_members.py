import pytest
from httpx import AsyncClient

from tests.utils import MockGroup, MockUser


@pytest.mark.asyncio
async def test_not_authorized_user_cannot_read_group_members(
    client: AsyncClient, not_empty_group: MockGroup
):
    result = await client.get(f"v1/groups/{not_empty_group.id}/users")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


@pytest.mark.asyncio
async def test_not_member_of_group_cannot_read_group_members(
    client: AsyncClient, not_empty_group: MockGroup, simple_user: MockUser
):
    result = await client.get(
        f"v1/groups/{not_empty_group.id}/users",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


@pytest.mark.asyncio
async def test_member_of_group_can_read_group_members(
    client: AsyncClient, not_empty_group: MockGroup
):
    user = not_empty_group.members[0]
    result = await client.get(
        f"v1/groups/{not_empty_group.id}/users",
        headers={
            "Authorization": f"Bearer {user.token}",
        },
    )
    assert result.status_code == 200
    members = [
        {
            "id": user.id,
            "is_superuser": user.is_superuser,
            "username": user.username,
        }
        for user in not_empty_group.members
    ]
    members.sort(key=lambda x: x["username"])
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 3,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": members,
    }


@pytest.mark.asyncio
async def test_admin_of_group_can_read_group_members(
    client: AsyncClient, empty_group: MockGroup, not_empty_group: MockGroup
):
    result = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={
            "Authorization": f"Bearer {empty_group.admin.token}",
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 0,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [],
    }

    result = await client.get(
        f"v1/groups/{not_empty_group.id}/users",
        headers={
            "Authorization": f"Bearer {empty_group.admin.token}",
        },
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


@pytest.mark.asyncio
async def test_admin_of_group_can_read_group_members(
    client: AsyncClient,
    empty_group: MockGroup,
    not_empty_group: MockGroup,
    superuser: MockUser,
):
    result = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 0,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [],
    }

    result = await client.get(
        f"v1/groups/{not_empty_group.id}/users",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    assert result.status_code == 200
    members = [
        {
            "id": user.id,
            "is_superuser": user.is_superuser,
            "username": user.username,
        }
        for user in not_empty_group.members
    ]
    members.sort(key=lambda x: x["username"])
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 3,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": members,
    }
