import pytest
from httpx import AsyncClient

from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_member_of_group_can_read_by_id(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.get(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "data": {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "owner_id": group.owner_id,
        },
        "role": user.role.value,
    }
    assert result.status_code == 200


async def test_groupless_user_cannot_read_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    # Act
    result = await client.get(
        f"v1/groups/{empty_group.id}",
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


async def test_other_member_group_cannot_read_group(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    simple_user: MockUser,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
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


async def test_superuser_can_read_group(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
):
    # Act
    result = await client.get(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    assert result.json() == {
        "data": {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "owner_id": group.owner_id,
        },
        "role": superuser.role.value,
    }
    assert result.status_code == 200


async def test_not_authorized_user_cannot_read_by_id(
    client: AsyncClient,
    empty_group: MockGroup,
):
    # Act
    result = await client.get(f"v1/groups/{empty_group.id}")
    # Assert
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }
    assert result.status_code == 401


async def test_member_of_group_read_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.get(
        "v1/groups/-1",
        headers={"Authorization": f"Bearer {user.token}"},
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


async def test_superuser_read_unknown_group_error(
    client: AsyncClient,
    superuser: MockUser,
):
    # Act
    result = await client.get(
        "v1/groups/-1",
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
