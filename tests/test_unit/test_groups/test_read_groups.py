import random
import string
from collections.abc import Callable

import pytest
from httpx import AsyncClient

from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


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
                "data": {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "owner_id": group.owner_id,
                },
                "role": role_guest_plus,
            },
        ],
    }
    assert result.status_code == 200, result.json()


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
    assert result.status_code == 200, result.json()


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
                "data": {
                    "id": empty_group.id,
                    "name": empty_group.name,
                    "description": empty_group.description,
                    "owner_id": empty_group.owner_id,
                },
                "role": UserTestRoles.Superuser,
            },
            {
                "data": {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "owner_id": group.owner_id,
                },
                "role": UserTestRoles.Superuser,
            },
        ],
    }
    assert result.status_code == 200, result.json()


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
    assert result.status_code == 401, result.json()


@pytest.mark.parametrize(
    "role,expected_total,expected_roles",
    [
        (None, 4, {"Guest", "Developer", "Maintainer", "Owner"}),  # No role filter
        ("Guest", 4, {"Guest", "Developer", "Maintainer", "Owner"}),
        ("Developer", 3, {"Developer", "Maintainer", "Owner"}),
        ("Maintainer", 2, {"Maintainer", "Owner"}),
        ("Owner", 1, {"Owner"}),
        ("Superuser", 0, set()),
    ],
)
async def test_filter_groups_by_role(
    client: AsyncClient,
    user_with_many_roles: MockUser,
    role: str,
    expected_total: int,
    expected_roles: set,
):
    role_query = f"?role={role}" if role else ""
    result = await client.get(
        f"v1/groups{role_query}",
        headers={"Authorization": f"Bearer {user_with_many_roles.token}"},
    )

    assert result.status_code == 200, result.json()
    response_json = result.json()

    assert response_json["meta"]["total"] == expected_total
    assert len(response_json["items"]) == expected_total

    assert {item.get("role") for item in response_json["items"]} == expected_roles


@pytest.mark.parametrize(
    "role,expected_total",
    [
        (None, 4),  # No role filter
        ("Guest", 4),
        ("Developer", 4),
        ("Maintainer", 4),
        ("Owner", 4),
        ("Superuser", 4),
    ],
)
async def test_filter_groups_not_applied_to_superuser(
    client: AsyncClient,
    user_with_many_roles: MockUser,  # keep it, needed to create different groups
    superuser: MockUser,
    role: str,
    expected_total: int,
):
    role_query = f"?role={role}" if role else ""
    result = await client.get(
        f"v1/groups{role_query}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert result.status_code == 200, result.json()
    response_json = result.json()

    assert response_json["meta"]["total"] == expected_total
    assert len(response_json["items"]) == expected_total

    for item in response_json["items"]:
        assert item.get("role") == UserTestRoles.Superuser


@pytest.mark.parametrize(
    "search_value, expected_total",
    [
        ("group_for", 4),
        ("group_for_Owner", 1),
        ("group_for_Maintainer", 1),
        ("group_for_Developer", 1),
        ("group_for_Guest", 1),
    ],
    ids=[
        "search_by_name_partial_match",
        "owner_search_by_group_name",
        "maintainer_search_by_group_name",
        "developer_search_by_group_name",
        "guest_search_by_group_name",
    ],
)
async def test_search_groups_with_query(
    client: AsyncClient,
    user_with_many_roles: MockUser,
    search_value: str,
    expected_total: int,
):

    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {user_with_many_roles.token}"},
        params={"search_query": search_value},
    )

    assert result.status_code == 200, result.json()
    assert result.json()["meta"]["total"] == expected_total
    assert len(result.json()["items"]) == expected_total


@pytest.mark.parametrize(
    "search_value_extractor",
    [
        lambda group: group.name,
        lambda group: "_".join(group.name.split("_")[:1]),
        lambda group: "_".join(group.name.split("_")[:2]),
        lambda group: "_".join(group.name.split("_")[-1:]),
    ],
    ids=[
        "guest_search_by_name_full_match",
        "guest_search_by_name_first_token",
        "guest_search_by_name_two_tokens",
        "guest_search_by_name_last_token",
    ],
)
async def test_superuser_search_groups_with_query(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    search_value_extractor: Callable,
):
    search_query = search_value_extractor(group)

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
                "data": {
                    "id": group.id,
                    "name": group.name,
                    "description": group.description,
                    "owner_id": group.owner_id,
                },
                "role": superuser.role,
            },
        ],
    }
    assert result.status_code == 200, result.json()


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

    assert result.status_code == 200, result.json()
    assert result.json()["items"] == []
