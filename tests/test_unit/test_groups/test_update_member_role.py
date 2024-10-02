import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_owner_of_group_can_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    group_owner = group.get_member_of_role(UserTestRoles.Owner)
    # Act
    result = await client.patch(
        f"v1/groups/{group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    # Assert
    assert result.json() == {"role": role_guest_plus_without_owner}
    assert result.status_code == 200


async def test_superuser_can_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    # Act
    result = await client.patch(
        f"v1/groups/{group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    # Assert
    assert result.json() == {"role": role_guest_plus_without_owner}
    assert result.status_code == 200


async def test_owner_of_group_can_not_update_user_role_with_wrong_role(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    # Act
    result = await client.patch(
        f"v1/groups/{group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "role": "Unknown",
        },
    )

    # Assert
    assert result.status_code == 422
    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "context": {"expected": "'Maintainer', 'Developer' or 'Guest'"},
                    "input": "Unknown",
                    "location": ["body", "role"],
                    "message": "Input should be 'Maintainer', 'Developer' or 'Guest'",
                    "code": "enum",
                },
            ],
        },
    }


async def test_maintainer_below_can_not_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    # Arrange
    updating_user = group.get_member_of_role(role_maintainer_or_below)
    user_to_update = group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.patch(
        f"v1/groups/{group.id}/users/{user_to_update.user.id}",
        headers={"Authorization": f"Bearer {updating_user.token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
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


async def test_other_group_member_can_not_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_guest_plus)
    group_member = group.get_member_of_role(role_guest_plus_without_owner)
    # Act
    result = await client.patch(
        f"v1/groups/{group.id}/users/{group_member.user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": UserTestRoles.Maintainer,
        },
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


async def test_superuser_update_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    # Act
    result = await client.patch(
        f"v1/groups/-1/users/{user.user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_update_unknown_user_error(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    role_guest_plus_without_owner: UserTestRoles,
):
    # Act
    result = await client.patch(
        f"v1/groups/{group.id}/users/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }


async def test_owner_of_group_update_unknown_user_error(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    # Arrange
    group.get_member_of_role(role_maintainer_or_below)
    # Act
    result = await client.patch(
        f"v1/groups/{group.id}/users/-1",
        headers={"Authorization": f"Bearer {group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }


async def test_owner_of_group_update_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    # Act
    result = await client.patch(
        f"v1/groups/-1/users/{user.user.id}",
        headers={"Authorization": f"Bearer {group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
