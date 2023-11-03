import pytest
from httpx import AsyncClient
from tests.utils import MockConnection, MockGroup, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_read_connection(
    client: AsyncClient, user_connection: MockConnection
):
    result = await client.get(f"v1/connections/{user_connection.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_owner_can_read_connection_of_self(
    client: AsyncClient,
    user_connection: MockConnection,
    simple_user: MockUser,
):
    result = await client.get(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }

    result = await client.get(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {user_connection.owner_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_connection.id,
        "description": user_connection.description,
        "group_id": user_connection.group_id,
        "user_id": user_connection.user_id,
        "name": user_connection.name,
        "connection_data": {
            "type": user_connection.data["type"],
            "database_name": user_connection.data["database_name"],
            "host": user_connection.data["host"],
            "port": user_connection.data["port"],
            "additional_params": user_connection.data["additional_params"],
        },
        "auth_data": {
            "type": user_connection.credentials.value["type"],
            "user": user_connection.credentials.value["user"],
        },
    }


async def test_group_admin_can_read_connection_of_his_group(
    client: AsyncClient,
    group_connection: MockConnection,
    simple_user: MockUser,
):
    result = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }

    result = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {group_connection.owner_group.admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "user_id": group_connection.user_id,
        "name": group_connection.name,
        "connection_data": {
            "type": group_connection.data["type"],
            "database_name": group_connection.data["database_name"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "additional_params": group_connection.data["additional_params"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }


async def test_group_admin_cannot_read_connection_of_other(
    client: AsyncClient,
    group_connection: MockConnection,
    user_connection: MockConnection,
    empty_group: MockGroup,
):
    for connection in group_connection, user_connection:
        result = await client.get(
            f"v1/connections/{connection.id}",
            headers={"Authorization": f"Bearer {empty_group.admin.token}"},
        )
        assert result.status_code == 404
        assert result.json() == {
            "ok": False,
            "status_code": 404,
            "message": "Connection not found",
        }


async def test_superuser_can_read_all_connections(
    client: AsyncClient,
    superuser: MockUser,
    user_connection: MockConnection,
    group_connection: MockConnection,
):
    result = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "user_id": group_connection.user_id,
        "name": group_connection.name,
        "connection_data": {
            "type": group_connection.data["type"],
            "database_name": group_connection.data["database_name"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "additional_params": group_connection.data["additional_params"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }

    result = await client.get(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_connection.id,
        "description": user_connection.description,
        "group_id": user_connection.group_id,
        "user_id": user_connection.user_id,
        "name": user_connection.name,
        "connection_data": {
            "type": user_connection.data["type"],
            "database_name": user_connection.data["database_name"],
            "host": user_connection.data["host"],
            "port": user_connection.data["port"],
            "additional_params": user_connection.data["additional_params"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }

    result = await client.get(
        f"v1/connections/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }
