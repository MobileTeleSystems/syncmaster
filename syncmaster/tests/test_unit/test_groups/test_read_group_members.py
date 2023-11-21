import pytest
from httpx import AsyncClient
from tests.utils import MockConnection, MockGroup, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_member_of_group_can_read_group_members(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.get(
        f"v1/groups/{group.id}/users",
        headers={
            "Authorization": f"Bearer {user.token}",
        },
    )

    # Assert
    members = [
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
        for user in (
            group.get_member_of_role(TestUserRoles.Maintainer),
            group.get_member_of_role(TestUserRoles.User),
            group.get_member_of_role(TestUserRoles.Guest),
        )
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
    assert result.status_code == 200


async def test_groupless_user_cannot_read_group_members(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
):
    # Act
    result = await client.get(
        f"v1/groups/{group.id}/users",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }
    assert result.status_code == 404


async def test_other_group_member_cannot_read_group_members(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.get(
        f"v1/groups/{group.id}/users",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }
    assert result.status_code == 404


async def test_superuser_can_read_group_members(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
):
    # Act
    result = await client.get(
        f"v1/groups/{group.id}/users",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    members = [
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
        for user in (
            group.get_member_of_role(TestUserRoles.Maintainer),
            group.get_member_of_role(TestUserRoles.User),
            group.get_member_of_role(TestUserRoles.Guest),
        )
    ]
    members.sort(key=lambda x: x["username"])
    # Assert
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
    assert result.status_code == 200


async def test_not_authorized_user_cannot_read_group_members(client: AsyncClient, group: MockGroup):
    # Act
    result = await client.get(f"v1/groups/{group.id}/users")
    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_member_of_group_cannot_read_unknown_group_members_error(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.get(
        f"v1/groups/-1/users",
        headers={
            "Authorization": f"Bearer {user.token}",
        },
    )

    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_read_unknown_group_members_error(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
):
    # Act
    result = await client.get(
        f"v1/groups/-1/users",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
