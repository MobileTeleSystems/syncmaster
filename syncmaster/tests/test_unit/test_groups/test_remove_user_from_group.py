import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_not_authorized_user_cannot_remove_user_from_group(client: AsyncClient, group: MockGroup):
    member = group.get_member_of_role(TestUserRoles.User)
    result = await client.delete(f"v1/groups/{group.id}/users/{member.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_not_member_group_cannot_remove_user_from_group(
    client: AsyncClient, group: MockGroup, simple_user: MockUser
):
    member = group.get_member_of_role(TestUserRoles.User)
    result = await client.delete(
        f"v1/groups/{group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


async def test_member_of_group_can_delete_self_from_group(client: AsyncClient, group: MockGroup):
    member = group.get_member_of_role(TestUserRoles.User)
    result = await client.delete(
        f"v1/groups/{group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {member.token}"},
    )
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully removed from group",
    }
    assert result.status_code == 200

    result = await client.get(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {member.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


async def test_member_of_group_cannot_delete_others_from_group(client: AsyncClient, group: MockGroup):
    first_member = group.get_member_of_role(TestUserRoles.Maintainer)
    second_member = group.get_member_of_role(TestUserRoles.User)

    result = await client.delete(
        f"v1/groups/{group.id}/users/{first_member.id}",
        headers={"Authorization": f"Bearer {second_member.token}"},
    )
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }
    assert result.status_code == 403

    result = await client.get(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {first_member.token}"},
    )

    assert result.json() == {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "admin_id": group.admin_id,
    }
    assert result.status_code == 200


async def test_owner_of_group_can_delete_anyone_from_group(client: AsyncClient, group: MockGroup):
    for member in (
        group.get_member_of_role(TestUserRoles.Maintainer),
        group.get_member_of_role(TestUserRoles.User),
        group.get_member_of_role(TestUserRoles.Guest),
    ):
        result = await client.delete(
            f"v1/groups/{group.id}/users/{member.id}",
            headers={"Authorization": f"Bearer {group.get_member_of_role(TestUserRoles.Owner).token}"},
        )
        assert result.status_code == 200
        assert result.json() == {
            "ok": True,
            "status_code": 200,
            "message": "User was successfully removed from group",
        }

    result = await client.get(
        f"v1/groups/{group.id}/users",
        headers={"Authorization": f"Bearer {group.get_member_of_role(TestUserRoles.Owner).token}"},
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


async def test_cannot_delete_someone_twice_from_group(client: AsyncClient, group: MockGroup):
    member = group.get_member_of_role(TestUserRoles.User)
    result = await client.delete(
        f"v1/groups/{group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {group.get_member_of_role(TestUserRoles.Owner).token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully removed from group",
    }

    result = await client.delete(
        f"v1/groups/{group.id}/users/{member.id}",
        headers={"Authorization": f"Bearer {group.get_member_of_role(TestUserRoles.Owner).token}"},
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "User already is not group member",
    }


async def test_superuser_can_delete_from_any_group(
    client: AsyncClient,
    group: MockGroup,
    empty_group: MockGroup,
    superuser: MockUser,
):
    member = group.get_member_of_role(TestUserRoles.User)
    result = await client.delete(
        f"v1/groups/{group.id}/users/{member.id}",
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
        json={
            "role": TestUserRoles.User,
        },
    )
    assert result.status_code == 200
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
