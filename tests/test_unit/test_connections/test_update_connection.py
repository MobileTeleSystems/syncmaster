import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, MockGroup, MockTransfer, MockUser, UserTestRoles
from tests.test_unit.utils import fetch_connection_json

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_developer_plus_can_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "name": "New connection name", "type": group_connection.type},
    )

    assert result.json() == {
        "id": group_connection.id,
        "name": "New connection name",
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
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
    assert result.status_code == 200, result.json()


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "oracle",
            {
                "host": "127.0.0.1",
                "port": 1521,
                "sid": "sid_name",
            },
            {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_oracle_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    group_connection.connection.group.id
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            **connection_json,
            "type": "oracle",
            "connection_data": {
                "host": "127.0.1.1",
                "port": 1522,
                "sid": "new_sid_name",
            },
            "auth_data": {
                "type": "basic",
                "user": "new_user",
                "password": "new_secret",
            },
        },
    )

    assert result.status_code == 200, result.json()
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
            "host": "127.0.1.1",
            "port": 1522,
            "sid": "new_sid_name",
            "additional_params": {},
            "service_name": None,
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": "new_user",
        },
    }


async def test_groupless_user_cannot_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    simple_user: MockUser,
):
    connection_json = {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "database_name": group_connection.data["database_name"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
            "password": "password",
        },
    }

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json=connection_json,
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }


async def test_check_name_field_validation_on_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "name": "", "type": group_connection.type},
    )

    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "context": {"min_length": 1},
                    "input": "",
                    "location": ["body", "postgres", "name"],
                    "message": "String should have at least 1 character",
                    "code": "string_too_short",
                },
            ],
        },
    }


async def test_group_member_cannot_update_other_group_connection(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)
    connection_json = {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "database_name": group_connection.data["database_name"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
            "password": "password",
        },
    }

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json=connection_json,
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }


async def test_superuser_can_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
):
    connection_json = await fetch_connection_json(client, superuser.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={**connection_json, "type": "postgres", "name": "New connection name"},
    )

    assert result.json() == {
        "id": group_connection.id,
        "name": "New connection name",
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
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
    assert result.status_code == 200, result.json()


async def test_update_connection_data_fields(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "connection_data": {"host": "localhost", "port": 5432, "database_name": "db"}},
    )

    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
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
    assert result.status_code == 200, result.json()


async def test_update_connection_auth_data(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            **connection_json,
            "type": "postgres",
            "auth_data": {"type": "basic", "user": "new_user", "password": "new_password"},
        },
    )

    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
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
    assert result.status_code == 200, result.json()


async def test_superuser_cannot_update_connection_auth_data_type_without_secret(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
):
    connection_json = await fetch_connection_json(client, superuser.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            **connection_json,
            "connection_data": {
                "host": "localhost",
                "port": 9000,
                "bucket": "new_bucket",
            },
            "type": "s3",
            "auth_data": {"type": "s3", "access_key": "s3_key"},
        },
    )

    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "You cannot update the connection auth type without providing a new secret value.",
            "details": None,
        },
    }
    assert result.status_code == 409, result.json()


async def test_unauthorized_user_cannot_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
):
    result = await client.put(
        f"v1/connections/{group_connection.id}",
        json={"name": "New connection name"},
    )

    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }
    assert result.status_code == 401, result.json()


async def test_developer_plus_cannot_update_unknown_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        "v1/connections/-1",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "type": "postgres", "name": "New connection name"},
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }


async def test_superuser_cannot_update_unknown_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
):
    connection_json = await fetch_connection_json(client, superuser.token, group_connection)

    result = await client.put(
        "v1/connections/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={**connection_json, "type": "postgres", "name": "New connection name"},
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "oracle",
            {
                "host": "127.0.0.1",
                "port": 1521,
                "sid": "sid_name",
            },
            {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_update_oracle_connection_both_sid_and_service_name_error(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    group_id = group_connection.connection.group.id

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group_id,
            "name": "New connection",
            "description": "",
            "type": "oracle",
            "connection_data": {
                "host": "127.0.0.1",
                "port": 1521,
                "sid": "sid_name",
                "service_name": "service_name",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )

    assert result.status_code == 422, result.json()
    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "context": {},
                    "input": {
                        "host": "127.0.0.1",
                        "port": 1521,
                        "service_name": "service_name",
                        "sid": "sid_name",
                    },
                    "location": ["body", "oracle", "connection_data"],
                    "message": "Value error, You must specify either sid or service_name but not both",
                    "code": "value_error",
                },
            ],
        },
    }


async def test_maintainer_plus_cannot_update_connection_type_with_linked_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_maintainer_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_transfer.source_connection)

    result = await client.put(
        f"v1/connections/{group_transfer.source_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            **connection_json,
            "name": "New connection name",
            "type": "oracle",
        },
    )

    assert result.status_code == 409, result.json()
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "You cannot update the connection type of a connection already associated with a transfer.",
            "details": None,
        },
    }


async def test_guest_cannot_update_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
):
    user = group_connection.owner_group.get_member_of_role(UserTestRoles.Guest)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "type": "postgres", "name": "New connection name"},
    )

    assert result.status_code == 403, result.json()
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
