import pytest
from httpx import AsyncClient
from tests.utils import MockConnection, MockGroup, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
):
    result = await client.patch(f"v1/connections/{group_connection.id}", json={"name": "New connection name"})
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_groupless_user_cannot_update_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
    simple_user: MockUser,
):
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_in_group_user_can_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
):
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={
            "Authorization": f"Bearer {group_connection.owner_group.get_member_of_role(TestUserRoles.User).token}"
        },
        json={"name": "New connection name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": "New connection name",
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "additional_params": group_connection.data["additional_params"],
            "database_name": group_connection.data["database_name"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }


async def test_superuser_can_update_user_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
):
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": "New connection name",
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "additional_params": group_connection.data["additional_params"],
            "database_name": group_connection.data["database_name"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }


async def test_group_owner_can_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
):
    admin = group_connection.owner_group.get_member_of_role(TestUserRoles.Owner)
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": "New connection name",
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "additional_params": group_connection.data["additional_params"],
            "database_name": group_connection.data["database_name"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }


async def test_group_owner_cannot_update_other_group_connection(
    client: AsyncClient, empty_group: MockGroup, group_connection: MockConnection
):
    other_admin = empty_group.get_member_of_role("Owner")
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {other_admin.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_superuser_can_update_group_connection(
    client: AsyncClient, group_connection: MockConnection, superuser: MockUser
):
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": "New connection name",
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "additional_params": group_connection.data["additional_params"],
            "database_name": group_connection.data["database_name"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }


async def test_update_connection_data_fields(
    client: AsyncClient,
    group_connection: MockConnection,
):
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={
            "Authorization": f"Bearer {group_connection.owner_group.get_member_of_role(TestUserRoles.User).token}"
        },
        json={"connection_data": {"host": "localhost"}},
    )
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "loc": ["body", "connection_data"],
                "msg": "Discriminator 'type' is missing in value",
                "type": "value_error.discriminated_union.missing_discriminator",
                "ctx": {"discriminator_key": "type"},
            }
        ]
    }

    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={
            "Authorization": f"Bearer {group_connection.owner_group.get_member_of_role(TestUserRoles.User).token}"
        },
        json={"connection_data": {"type": "postgres", "host": "localhost"}},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": "localhost",
            "port": group_connection.data["port"],
            "additional_params": group_connection.data["additional_params"],
            "database_name": group_connection.data["database_name"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }


async def test_update_connection_auth_data_fields(
    client: AsyncClient,
    group_connection: MockConnection,
):
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={
            "Authorization": f"Bearer {group_connection.owner_group.get_member_of_role(TestUserRoles.User).token}"
        },
        json={"auth_data": {"type": "postgres", "user": "new_user"}},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": "127.0.0.1",
            "port": group_connection.data["port"],
            "additional_params": group_connection.data["additional_params"],
            "database_name": group_connection.data["database_name"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": "new_user",
        },
    }
