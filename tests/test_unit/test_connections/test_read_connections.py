import random
import string
from typing import Any

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.settings import Settings
from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_guest_plus_can_read_connections(
    client: AsyncClient,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
    settings: Settings,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"group_id": group_connection.connection.group_id},
    )

    # Assert
    assert result.status_code == 200
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
                "id": group_connection.id,
                "description": group_connection.description,
                "group_id": group_connection.group_id,
                "name": group_connection.name,
                "connection_data": {
                    "type": group_connection.data["type"],
                    "host": group_connection.data["host"],
                    "port": group_connection.data["port"],
                    "database_name": group_connection.data["database_name"],
                    "additional_params": group_connection.data["additional_params"],
                },
                "auth_data": {
                    "type": group_connection.credentials.value["type"],
                    "user": group_connection.credentials.value["user"],
                },
            },
        ],
    }


async def test_other_group_member_cannot_read_group_connections(
    client: AsyncClient,
    session: AsyncSession,
    settings: Settings,
    group: MockGroup,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"group_id": group_connection.connection.group_id},
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


async def test_groupless_user_cannot_read_group_connections(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    settings: Settings,
    group_connection: MockConnection,
):
    # Act
    result = await client.get(
        "v1/connections",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        params={"group_id": group_connection.connection.group_id},
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


async def test_superuser_can_read_connections(
    client: AsyncClient,
    superuser: MockUser,
    group_connection: MockConnection,
):
    # Act
    result = await client.get(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": group_connection.connection.group_id},
    )

    # Assert
    assert result.status_code == 200
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
                "id": group_connection.id,
                "description": group_connection.description,
                "group_id": group_connection.group_id,
                "name": group_connection.name,
                "connection_data": {
                    "type": group_connection.data["type"],
                    "host": group_connection.data["host"],
                    "port": group_connection.data["port"],
                    "database_name": group_connection.data["database_name"],
                    "additional_params": group_connection.data["additional_params"],
                },
                "auth_data": {
                    "type": group_connection.credentials.value["type"],
                    "user": group_connection.credentials.value["user"],
                },
            },
        ],
    }


async def test_unauthorized_user_cannot_read_connections(client: AsyncClient):
    # Act
    result = await client.get("v1/connections")

    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_guest_plus_cannot_read_unknown_group_error(
    client: AsyncClient,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
    settings: Settings,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"group_id": -1},
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


async def test_superuser_cannot_read_from_unknown_group_error(
    client: AsyncClient,
    superuser: MockUser,
    group_connection: MockConnection,
):
    # Act
    result = await client.get(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": -1},
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


@pytest.mark.parametrize(
    "search_value_extractor",
    [
        lambda connection: connection.name,
        lambda connection: "_".join(connection.name.split("_")[:1]),
        lambda connection: connection.data.get("host"),
        lambda connection: ".".join(connection.name.split("_")[:1]),
    ],
    ids=["name", "name_token", "hostname", "hostname_token"],
)
async def test_search_connections_with_query(
    client: AsyncClient,
    superuser: MockUser,
    group_connection: MockConnection,
    search_value_extractor,
):
    search_query = search_value_extractor(group_connection.connection)

    result = await client.get(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": group_connection.connection.group_id, "search_query": search_query},
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
                "id": group_connection.id,
                "description": group_connection.description,
                "group_id": group_connection.group_id,
                "name": group_connection.name,
                "connection_data": {
                    "type": group_connection.data["type"],
                    "host": group_connection.data["host"],
                    "port": group_connection.data["port"],
                    "database_name": group_connection.data["database_name"],
                    "additional_params": group_connection.data["additional_params"],
                },
                "auth_data": {
                    "type": group_connection.credentials.value["type"],
                    "user": group_connection.credentials.value["user"],
                },
            },
        ],
    }
    assert result.status_code == 200


async def test_search_connections_with_nonexistent_query(
    client: AsyncClient,
    superuser: MockUser,
    group_connection: MockConnection,
):
    random_search_query = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))

    result = await client.get(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": group_connection.connection.group_id, "search_query": random_search_query},
    )

    assert result.status_code == 200
    assert result.json()["items"] == []


@pytest.mark.parametrize(
    "filter_params, expected_total",
    [
        ({}, 5),  # No filters applied, expecting all connections
        ({"type": ["oracle"]}, 1),
        ({"type": ["postgres", "hive"]}, 2),
        ({"type": ["postgres", "hive", "oracle", "hdfs", "s3"]}, 5),
    ],
    ids=[
        "no_filters",
        "single_type",
        "multiple_types",
        "all_types",
    ],
)
async def test_filter_connections(
    client: AsyncClient,
    superuser: MockUser,
    filter_params: dict[str, Any],
    expected_total: int,
    group_connections: list[MockConnection],
):
    # Arrange
    params = {**filter_params, "group_id": group_connections[0].connection.group_id}

    # Act
    result = await client.get(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params=params,
    )

    # Assert
    assert result.status_code == 200
    assert result.json()["meta"]["total"] == expected_total
    assert len(result.json()["items"]) == expected_total

    # check that the types match
    if "type" in params and params["type"]:
        returned_types = [conn["connection_data"]["type"] for conn in result.json()["items"]]
        assert all(type in params["type"] for type in returned_types)


async def test_filter_connections_unknown_type(
    client: AsyncClient,
    superuser: MockUser,
    group_connections: list[MockConnection],
):
    # Arrange
    params = {"type": "unknown", "group_id": group_connections[0].connection.group_id}

    # Act
    result = await client.get(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params=params,
    )

    # Assert
    assert result.status_code == 422
    assert result.json()["error"]["details"][0]["code"] == "enum"
