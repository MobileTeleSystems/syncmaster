import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, MockGroup, MockUser, TestUserRoles

from app.config import Settings

pytestmark = [pytest.mark.asyncio]


async def test_guest_plus_can_read_connections(
    client: AsyncClient,
    group_connection: MockConnection,
    role_guest_plus: TestUserRoles,
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
    role_guest_plus: TestUserRoles,
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
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
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
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
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
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_guest_plus_cannot_read_unknown_group_error(
    client: AsyncClient,
    group_connection: MockConnection,
    role_guest_plus: TestUserRoles,
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
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
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
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404
