import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_owner_can_delete_anyone_from_group(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    group_owner = group.get_member_of_role(UserTestRoles.Owner)
    # Act
    result = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {group_owner.token}"},
    )
    # Assert
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully removed from group",
    }
    assert result.status_code == 200


async def test_groupless_user_cannot_remove_user_from_group(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    # Act
    result = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_other_group_member_cannot_remove_user_from_group(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    other_group_member = group_connection.owner_group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {other_group_member.token}"},
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_maintainer_and_user_can_delete_self_from_group(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below_without_guest: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below_without_guest)
    # Act
    result = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully removed from group",
    }
    assert result.status_code == 200


async def test_owner_cannot_delete_self_from_group(
    client: AsyncClient,
    group: MockGroup,
):
    # Arrange
    user = group.get_member_of_role(UserTestRoles.Owner)
    # Act
    result = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "User already is not group member",
            "details": None,
        },
    }
    assert result.status_code == 409


async def test_maintainer_or_below_cannot_delete_others_from_group(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus: UserTestRoles,
):
    if role_maintainer_or_below != role_guest_plus:
        # Arrange
        user = group.get_member_of_role(role_maintainer_or_below)
        other_group_member = group.get_member_of_role(role_guest_plus)
        # Act
        result = await client.delete(
            f"v1/groups/{group.id}/users/{other_group_member.id}",
            headers={"Authorization": f"Bearer {user.token}"},
        )
        # Assert
        assert result.json() == {
            "error": {
                "code": "forbidden",
                "message": "You have no power here",
                "details": None,
            },
        }
        assert result.status_code == 403


async def test_superuser_can_delete_user_from_group(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    # Act
    result = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully removed from group",
    }
    assert result.status_code == 200


async def test_not_authorized_user_cannot_remove_user_from_group(client: AsyncClient, group: MockGroup):
    # Arrange
    user = group.get_member_of_role(UserTestRoles.Developer)
    # Act
    result = await client.delete(f"v1/groups/{group.id}/users/{user.id}")
    # Assert
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }
    assert result.status_code == 401


async def test_owner_delete_unknown_user_error(
    client: AsyncClient,
    group: MockGroup,
):
    # Arrange
    group_owner = group.get_member_of_role(UserTestRoles.Owner)
    # Act
    result = await client.delete(
        f"v1/groups/{group.id}/users/-1",
        headers={"Authorization": f"Bearer {group_owner.token}"},
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "User already is not group member",
            "details": None,
        },
    }
    assert result.status_code == 409


async def test_owner_delete_user_from_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
):
    # Arrange
    group_owner = group.get_member_of_role(UserTestRoles.Owner)
    user = group.get_member_of_role(role_maintainer_or_below)
    # Act
    result = await client.delete(
        f"v1/groups/-1/users/{user.user.id}",
        headers={"Authorization": f"Bearer {group_owner.token}"},
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_superuser_delete_unknown_user_error(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
):
    # Act
    result = await client.delete(
        f"v1/groups/{group.id}/users/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "User already is not group member",
            "details": None,
        },
    }
    assert result.status_code == 409


async def test_superuser_delete_user_from_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    # Act
    result = await client.delete(
        f"v1/groups/-1/users/{user.user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404
