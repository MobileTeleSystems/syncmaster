import pytest
from httpx import AsyncClient

from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_group_member_can_read_groups(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
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
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "owner_id": group.owner_id,
            }
        ],
    }
    assert result.status_code == 200


async def test_groupless_user_cannot_get_any_groups(
    client: AsyncClient,
    simple_user: MockUser,
    group: MockGroup,  # do not delete this group, it is not used but is needed to show that the group is not read
):
    # Act
    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    # Assert
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
    assert result.status_code == 200


async def test_superuser_can_read_all_groups(
    client: AsyncClient,
    superuser: MockUser,
    empty_group: MockGroup,
    group: MockGroup,
):
    # Act
    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 2,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": empty_group.id,
                "name": empty_group.name,
                "description": empty_group.description,
                "owner_id": empty_group.owner_id,
            },
            {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "owner_id": group.owner_id,
            },
        ],
    }
    assert result.status_code == 200


async def test_unauthorized_user_cannot_read_groups(
    client: AsyncClient,
):
    # Act
    result = await client.get("v1/groups")
    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
    assert result.status_code == 401
