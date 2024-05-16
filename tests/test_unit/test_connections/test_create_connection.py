import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.config import Settings
from syncmaster.db.models import AuthData, Connection
from syncmaster.db.repositories.utils import decrypt_auth_data
from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_developer_plus_can_create_connection(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
    event_loop,
    request,
):
    # Arrange
    user = group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
                "user": "user",
                "password": "secret",
            },
        },
    )

    connection = (
        await session.scalars(
            select(Connection).filter_by(
                name="New connection",
            ),
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            ),
        )
    ).one()

    def delete_rows():
        async def afin():
            await session.delete(creds)
            await session.delete(connection)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    # Assert
    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert result.json() == {
        "id": connection.id,
        "name": connection.name,
        "description": connection.description,
        "group_id": connection.group_id,
        "connection_data": {
            "type": connection.data["type"],
            "host": connection.data["host"],
            "port": connection.data["port"],
            "database_name": connection.data["database_name"],
            "additional_params": connection.data["additional_params"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "user": decrypted["user"],
        },
    }
    assert result.status_code == 200


async def test_developer_plus_can_create_oracle_connection(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
    event_loop,
    request,
):
    # Arrange
    user = group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "connection_data": {
                "type": "oracle",
                "host": "127.0.0.1",
                "port": 1521,
                "sid": "sid_name",
            },
            "auth_data": {
                "type": "oracle",
                "user": "user",
                "password": "secret",
            },
        },
    )

    connection = (
        await session.scalars(
            select(Connection).filter_by(
                name="New connection",
            ),
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            ),
        )
    ).one()

    def delete_rows():
        async def afin():
            await session.delete(creds)
            await session.delete(connection)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    # Assert
    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert result.json() == {
        "id": connection.id,
        "name": connection.name,
        "description": connection.description,
        "group_id": connection.group_id,
        "connection_data": {
            "type": connection.data["type"],
            "host": connection.data["host"],
            "port": connection.data["port"],
            "sid": connection.data["sid"],
            "service_name": connection.data["service_name"],
            "additional_params": connection.data["additional_params"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "user": decrypted["user"],
        },
    }
    assert result.status_code == 200


async def test_unauthorized_user_cannot_create_connection(
    client: AsyncClient,
    group_connection: MockConnection,
):
    result = await client.post(
        "v1/connections",
        json={
            "group_id": group_connection.id,
            "name": "New connection",
            "description": "",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
                "user": "user",
                "password": "secret",
            },
        },
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_check_fields_validation_on_create_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(UserTestRoles.Developer)

    # Act
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group_connection.id,
            "name": "",
            "description": "",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
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
                "ctx": {"min_length": 1},
                "input": "",
                "loc": ["body", "name"],
                "msg": "String should have at least 1 character",
                "type": "string_too_short",
            },
        ],
    }

    # Act
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group_connection.id,
            "name": None,
            "description": "",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
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
                "input": None,
                "loc": ["body", "name"],
                "msg": "Input should be a valid string",
                "type": "string_type",
            },
        ],
    }

    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group_connection.id,
            "name": "None",
            "description": None,
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
                "user": "user",
                "password": "secret",
            },
        },
    )
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "input": None,
                "loc": ["body", "description"],
                "msg": "Input should be a valid string",
                "type": "string_type",
            },
        ],
    }

    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group_connection.id,
            "name": "None",
            "description": "None",
            "connection_data": {
                "type": "POSTGRESQL",
                "host": "127.0.0.1",
                "port": 5432,
                "user": "user",
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
                "user": "user",
                "password": "secret",
            },
        },
    )
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "type": "union_tag_invalid",
                "loc": ["body", "connection_data"],
                "msg": "Input tag 'POSTGRESQL' found using 'type' does not match any of the expected tags: 'hive', 'oracle', 'postgres', 'hdfs', 's3'",
                "input": {
                    "type": "POSTGRESQL",
                    "host": "127.0.0.1",
                    "port": 5432,
                    "user": "user",
                    "database_name": "postgres",
                },
                "ctx": {
                    "discriminator": "'type'",
                    "tag": "POSTGRESQL",
                    "expected_tags": "'hive', 'oracle', 'postgres', 'hdfs', 's3'",
                },
            },
        ],
    }


async def test_other_group_member_cannot_create_group_connection(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": empty_group.id,
            "name": "New connection",
            "description": "",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
                "user": "user",
                "password": "secret",
            },
        },
    )

    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_superuser_can_create_connection(
    client: AsyncClient,
    superuser: MockUser,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
):
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": group.id,
            "name": "New connection from superuser",
            "description": "",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
                "user": "user",
                "password": "secret",
            },
        },
    )
    connection = (
        await session.scalars(
            select(Connection).filter_by(
                name="New connection from superuser",
                group_id=group.id,
            ),
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            ),
        )
    ).one()
    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert result.status_code == 200
    assert result.json() == {
        "id": connection.id,
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "connection_data": {
            "type": connection.data["type"],
            "host": connection.data["host"],
            "port": connection.data["port"],
            "database_name": connection.data["database_name"],
            "additional_params": connection.data["additional_params"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "user": decrypted["user"],
        },
    }


async def test_groupless_user_cannot_create_connection(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
    superuser: MockUser,
):
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
                "user": "user",
                "password": "secret",
            },
        },
    )
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_group_member_cannot_create_connection_with_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_guest_plus: UserTestRoles,
    event_loop,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": -1,
            "name": "New connection",
            "description": "",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
                "user": "user",
                "password": "secret",
            },
        },
    )

    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_cannot_create_connection_with_unknown_group_error(
    client: AsyncClient,
    superuser: MockUser,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
):
    # Act
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": -1,
            "name": "New connection from superuser",
            "description": "",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "postgres",
                "user": "user",
                "password": "secret",
            },
        },
    )

    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }


async def test_developer_plus_create_connection_with_not_same_types_error(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
    event_loop,
    request,
):
    # Arrange
    user = group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "oracle",
                "user": "user",
                "password": "secret",
            },
        },
    )

    # Assert
    assert result.json() == {
        "detail": [
            {
                "type": "value_error",
                "loc": ["body"],
                "msg": "Value error, Connection data and auth data must have same types",
                "input": {
                    "group_id": group.id,
                    "name": "New connection",
                    "description": "",
                    "connection_data": {
                        "type": "postgres",
                        "host": "127.0.0.1",
                        "port": 5432,
                        "database_name": "postgres",
                    },
                    "auth_data": {"type": "oracle", "user": "user", "password": "secret"},
                },
                "ctx": {"error": {}},
            }
        ]
    }
