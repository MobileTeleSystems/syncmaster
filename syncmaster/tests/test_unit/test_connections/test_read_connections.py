import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, MockUser, TestUserRoles

from app.config import Settings

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_read_connections(client: AsyncClient):
    result = await client.get("v1/connections")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_other_group_user_can_not_read_group_connections(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    settings: Settings,
    group_connection: MockConnection,
):
    result = await client.get(
        f"v1/connections?group_id={group_connection.connection.group_id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_group_owner_can_read_connections(
    client: AsyncClient,
    group_connection: MockConnection,
    settings: Settings,
):
    result = await client.get(
        f"v1/connections?group_id={group_connection.connection.group_id}",
        headers={
            "Authorization": f"Bearer {group_connection.owner_group.get_member_of_role(TestUserRoles.Owner).token}"
        },
    )

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


async def test_group_member_can_read_connections(
    client: AsyncClient,
    group_connection: MockConnection,
    settings: Settings,
):
    # Arrange
    group_member = group_connection.owner_group.get_member_of_role(TestUserRoles.User)

    # Act
    result = await client.get(
        f"v1/connections?group_id={group_connection.connection.group_id}",
        headers={"Authorization": f"Bearer {group_member.token}"},
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


async def test_superuser_can_read_connections(
    client: AsyncClient,
    superuser: MockUser,
    group_connection: MockConnection,
):
    result = await client.get(
        f"v1/connections?group_id={group_connection.connection.group_id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
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
