import random
import string

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
            },
        ],
    }
    assert result.status_code == 200


async def test_group_owner_can_read_empty_group(
    client: AsyncClient,
    empty_group: MockGroup,
):
    # Arrange
    owner = empty_group.get_member_of_role(UserTestRoles.Owner)
    # Act
    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {owner.token}"},
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
                "id": empty_group.id,
                "name": empty_group.name,
                "description": empty_group.description,
                "owner_id": empty_group.owner_id,
            },
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
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }
    assert result.status_code == 401


@pytest.mark.parametrize(
    "search_value_extractor",
    [
        lambda group: group.name,
        lambda group: "_".join(group.name.split("_")[:1]),
        lambda group: "_".join(group.name.split("_")[:2]),
        lambda group: "_".join(group.name.split("_")[-1:]),
    ],
    ids=[
        "search_by_name_full_match",
        "search_by_name_first_token",
        "search_by_name_two_tokens",
        "search_by_name_last_token",
    ],
)
async def test_search_groups_with_query(
    client: AsyncClient,
    superuser: MockUser,
    mock_group: MockGroup,
    search_value_extractor,
):
    search_query = search_value_extractor(mock_group)

    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"search_query": search_query},
    )

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
                "id": mock_group.id,
                "name": mock_group.name,
                "description": mock_group.description,
                "owner_id": mock_group.owner_id,
            },
        ],
    }
    assert result.status_code == 200


async def test_search_groups_with_nonexistent_query(
    client: AsyncClient,
    superuser: MockUser,
):
    random_search_query = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))

    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"search_query": random_search_query},
    )

    assert result.status_code == 200
    assert result.json()["items"] == []
