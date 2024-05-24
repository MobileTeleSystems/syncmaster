import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_developer_plus_can_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"name": "New connection name"},
    )

    # Assert
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
    assert result.status_code == 200


@pytest.mark.parametrize(
    "create_connection_data,create_connection_auth_data",
    [
        (
            {
                "type": "oracle",
                "host": "127.0.0.1",
                "port": 1521,
                "sid": "sid_name",
            },
            {
                "type": "oracle",
                "user": "user",
                "password": "secret",
            },
        ),
    ],
    indirect=True,
)
async def test_developer_plus_can_update_oracle_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    group_connection.connection.group.id

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "connection_data": {
                "type": "oracle",
                "host": "127.0.1.1",
                "sid": "new_sid_name",
            },
            "auth_data": {
                "type": "oracle",
                "user": "new_user",
            },
        },
    )

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": "127.0.1.1",
            "port": group_connection.data["port"],
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
    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"name": "New connection name"},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }
    assert result.status_code == 404


async def test_check_name_field_validation_on_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"name": ""},
    )

    # Assert
    assert result.json() == {
        "detail": [
            {
                "ctx": {"min_length": 1},
                "input": "",
                "loc": ["body", "name"],
                "msg": "String should have at least 1 character",
                "type": "string_too_short",
            },
        ],
    }


async def test_group_member_cannot_update_other_group_connection(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"name": "New connection name"},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }
    assert result.status_code == 404


async def test_superuser_can_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
):
    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New connection name"},
    )

    # Assert
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
    assert result.status_code == 200


async def test_update_connection_data_fields(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"connection_data": {"host": "localhost"}},
    )

    # Assert
    assert result.json() == {
        "detail": [
            {
                "ctx": {"discriminator": "'type'"},
                "input": {"host": "localhost"},
                "loc": ["body", "connection_data"],
                "msg": "Unable to extract tag using discriminator 'type'",
                "type": "union_tag_not_found",
            },
        ],
    }
    assert result.status_code == 422

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"connection_data": {"type": "postgres", "host": "localhost"}},
    )

    # Assert
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
    assert result.status_code == 200


async def test_update_connection_auth_data_all_felds(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"auth_data": {"type": "postgres", "user": "new_user", "password": "new_password"}},
    )

    # Assert
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
    assert result.status_code == 200


async def test_update_connection_auth_data_partial(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"auth_data": {"type": "postgres", "user": "new_user"}},
    )

    # Assert
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
    assert result.status_code == 200


async def test_unauthorized_user_cannot_update_connection(
    client: AsyncClient,
    group_connection: MockConnection,
):
    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        json={"name": "New connection name"},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
    assert result.status_code == 401


async def test_developer_plus_cannot_update_unknown_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.patch(
        "v1/connections/-1",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"name": "New connection name"},
    )

    # Assert
    assert result.json() == {
        "message": "Connection not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_cannot_update_unknown_connection_error(
    client: AsyncClient,
    superuser: MockUser,
):
    # Act
    result = await client.patch(
        "v1/connections/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New connection name"},
    )

    # Assert
    assert result.json() == {
        "message": "Connection not found",
        "ok": False,
        "status_code": 404,
    }


@pytest.mark.parametrize(
    "create_connection_data,create_connection_auth_data",
    [
        (
            {
                "type": "oracle",
                "host": "127.0.0.1",
                "port": 1521,
                "sid": "sid_name",
            },
            {
                "type": "oracle",
                "user": "user",
                "password": "secret",
            },
        ),
    ],
    indirect=True,
)
async def test_developer_plus_update_oracle_connection_both_sid_and_service_name_error(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    group_id = group_connection.connection.group.id

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group_id,
            "name": "New connection",
            "description": "",
            "connection_data": {
                "type": "oracle",
                "host": "127.0.0.1",
                "port": 1521,
                "sid": "sid_name",
                "service_name": "service_name",
            },
            "auth_data": {
                "type": "oracle",
                "user": "user",
                "password": "secret",
            },
        },
    )

    # Assert
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "ctx": {"error": {}},
                "input": {
                    "host": "127.0.0.1",
                    "port": 1521,
                    "service_name": "service_name",
                    "sid": "sid_name",
                    "type": "oracle",
                },
                "loc": ["body", "connection_data", "oracle"],
                "msg": "Value error, You must specify either sid or service_name but not both",
                "type": "value_error",
            },
        ],
    }


async def test_developer_plus_update_connection_with_diff_type_error(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New connection name",
            "connection_data": {
                "type": "postgres",
                "host": "new_host",
            },
            "auth_data": {
                "type": "oracle",
                "user": "new_user",
            },
        },
    )

    # Assert
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "ctx": {"error": {}},
                "input": {
                    "auth_data": {"type": "oracle", "user": "new_user"},
                    "connection_data": {"host": "new_host", "type": "postgres"},
                    "name": "New connection name",
                },
                "loc": ["body"],
                "msg": "Value error, Connection data and auth data must have same types",
                "type": "value_error",
            },
        ],
    }


async def test_maintainer_plus_cannot_update_connection_type_with_linked_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_maintainer_plus: UserTestRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.patch(
        f"v1/connections/{group_transfer.source_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New connection name",
            "connection_data": {
                "type": "oracle",
                "host": "new_host",
            },
        },
    )

    # Assert
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "You cannot update the connection type of a connection already associated with a transfer.",
    }
