import pytest
from httpx import AsyncClient

from tests.utils import MockGroup, MockUser

# check superuser can delete someone from group


@pytest.mark.asyncio
async def test_not_authorized_user_cannot_remove_user_from_group(
    client: AsyncClient, not_empty_group: MockGroup
):
    member = not_empty_group.members[0]
    result = await client.delete(f"v1/groups/{not_empty_group.id}/users/{member.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


@pytest.mark.asyncio
async def test_not_member_group_cannot_remove_user_from_group(
    client: AsyncClient, not_empty_group: MockGroup, simple_user: MockUser
):
    member = not_empty_group.members[0]
    result = await client.delete(
        f"v1/groups/{not_empty_group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


@pytest.mark.asyncio
async def test_member_of_group_can_delete_self_from_group(
    client: AsyncClient, not_empty_group: MockGroup
):
    member = not_empty_group.members[0]
    result = await client.delete(
        f"v1/groups/{not_empty_group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {member.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully removed from group",
    }

    result = await client.get(
        f"v1/groups/{not_empty_group.id}",
        headers={"Authorization": f"Bearer {member.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


@pytest.mark.asyncio
async def test_member_of_group_cannot_delete_others_from_group(
    client: AsyncClient, not_empty_group: MockGroup
):
    first_member = not_empty_group.members[0]
    second_member = not_empty_group.members[1]

    result = await client.delete(
        f"v1/groups/{not_empty_group.id}/users/{first_member.id}",
        headers={"Authorization": f"Bearer {second_member.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }

    result = await client.get(
        f"v1/groups/{not_empty_group.id}",
        headers={"Authorization": f"Bearer {first_member.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": not_empty_group.id,
        "name": not_empty_group.name,
        "description": not_empty_group.description,
        "admin_id": not_empty_group.admin_id,
    }


@pytest.mark.asyncio
async def test_admin_of_group_can_delete_anyone_from_group(
    client: AsyncClient, not_empty_group: MockGroup
):
    for member in not_empty_group.members:
        result = await client.delete(
            f"v1/groups/{not_empty_group.id}/users/{member.id}",
            headers={"Authorization": f"Bearer {not_empty_group.admin.token}"},
        )
        assert result.status_code == 200
        assert result.json() == {
            "ok": True,
            "status_code": 200,
            "message": "User was successfully removed from group",
        }

    result = await client.get(
        f"v1/groups/{not_empty_group.id}/users",
        headers={"Authorization": f"Bearer {not_empty_group.admin.token}"},
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


@pytest.mark.asyncio
async def test_cannot_delete_someone_twice_from_group(
    client: AsyncClient, not_empty_group: MockGroup
):
    member = not_empty_group.members[0]
    result = await client.delete(
        f"v1/groups/{not_empty_group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {not_empty_group.admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully removed from group",
    }

    result = await client.delete(
        f"v1/groups/{not_empty_group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {not_empty_group.admin.token}"},
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "User already not group member",
    }


@pytest.mark.asyncio
async def test_superuser_can_delete_from_any_group(
    client: AsyncClient,
    not_empty_group: MockGroup,
    empty_group: MockGroup,
    superuser: MockUser,
):
    member = not_empty_group.members[0]
    result = await client.delete(
        f"v1/groups/{not_empty_group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully removed from group",
    }

    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully added to group",
    }

    result = await client.delete(
        f"v1/groups/{empty_group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully removed from group",
    }
