import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_not_authorized_user_cannot_read_by_id(
    client: AsyncClient,
    empty_group: MockGroup,
):
    # check not authorized user cannot read by id
    result = await client.get(f"v1/groups/{empty_group.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_not_member_of_group_cannot_read_by_id(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


async def test_member_of_group_can_read_by_id(
    client: AsyncClient,
    group: MockGroup,
):
    member = group.get_member_of_role(TestUserRoles.User)
    result = await client.get(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {member.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group.id,
        "name": group.name,
        "description": group.description,
        "admin_id": group.admin_id,
    }


async def test_admin_of_group_can_read_by_id(
    client: AsyncClient,
    empty_group: MockGroup,
):
    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": empty_group.id,
        "name": empty_group.name,
        "description": empty_group.description,
        "admin_id": empty_group.admin_id,
    }


async def test_superuser_can_read_any_group_by_id(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    superuser: MockUser,
):
    for group in empty_group, group:
        result = await client.get(
            f"v1/groups/{group.id}",
            headers={"Authorization": f"Bearer {superuser.token}"},
        )
        assert result.status_code == 200
        assert result.json() == {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "admin_id": group.admin_id,
        }


async def test_superuser_cannot_read_group_by_incorrect_id(
    client: AsyncClient,
    superuser: MockUser,
):
    result = await client.get(
        "v1/groups/-3",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }
