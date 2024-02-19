import pytest
from httpx import AsyncClient
from tests.utils import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio]


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
                "ctx": {"limit_value": 1},
                "loc": ["body", "name"],
                "msg": "ensure this value has at least 1 characters",
                "type": "value_error.any_str.min_length",
            }
        ]
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
                "loc": ["body", "connection_data"],
                "msg": "Discriminator 'type' is missing in value",
                "type": "value_error.discriminated_union.missing_discriminator",
                "ctx": {"discriminator_key": "type"},
            }
        ]
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


async def test_update_connection_auth_data_fields(
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
