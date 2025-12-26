import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import AuthData, Connection
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_developer_plus_can_create_connection(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
    event_loop,
    request,
):
    user = group.get_member_of_role(role_developer_plus)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "type": "postgres",
            "connection_data": {
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )
    assert response.status_code == 200, response.text

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

    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert response.json() == {
        "id": connection.id,
        "name": connection.name,
        "description": connection.description,
        "group_id": connection.group_id,
        "type": connection.type,
        "connection_data": {
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


async def test_unauthorized_user_cannot_create_connection(
    client: AsyncClient,
    group_connection: MockConnection,
):
    response = await client.post(
        "v1/connections",
        json={
            "group_id": group_connection.id,
            "name": "New connection",
            "description": "",
            "type": "postgres",
            "connection_data": {
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )
    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


@pytest.mark.parametrize(
    ["name", "error"],
    [
        pytest.param(
            "aa",
            {
                "context": {"min_length": 3},
                "input": "aa",
                "location": ["body", "postgres", "name"],
                "message": "String should have at least 3 characters",
                "code": "string_too_short",
            },
            id="name_too_short",
        ),
        pytest.param(
            "a" * 129,
            {
                "context": {"max_length": 128},
                "input": "a" * 129,
                "location": ["body", "postgres", "name"],
                "message": "String should have at most 128 characters",
                "code": "string_too_long",
            },
            id="name_too_long",
        ),
    ],
)
async def test_check_name_field_validation_on_create_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
    name: str,
    error: dict,
):
    user = group_connection.owner_group.get_member_of_role(UserTestRoles.Developer)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group_connection.id,
            "name": name,
            "description": name,
            "type": "postgres",
            "connection_data": {
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )

    assert response.status_code == 422, response.text
    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [error],
        },
    }

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group_connection.id,
            "name": "New",
            "description": "New",
            "type": "POSTGRESQL",
            "connection_data": {
                "host": "127.0.0.1",
                "port": 5432,
                "user": "user",
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )

    assert response.status_code == 422, response.text
    message = response.json()["error"]["details"][0]["message"]
    assert message == (
        "Input tag 'POSTGRESQL' found using 'type' does not match any of the expected tags: "
        "'clickhouse', 'hive', 'iceberg', 'mssql', 'mysql', 'oracle', 'postgres', "
        "'ftp', 'ftps', 'hdfs', 's3', 'samba', 'sftp', 'webdav'"
    )


async def test_other_group_member_cannot_create_group_connection(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": empty_group.id,
            "name": "New connection",
            "description": "",
            "type": "postgres",
            "connection_data": {
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_superuser_can_create_connection(
    client: AsyncClient,
    superuser: MockUser,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
):
    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": group.id,
            "name": "New connection from superuser",
            "description": "",
            "type": "postgres",
            "connection_data": {
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )
    assert response.status_code == 200, response.text

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
    assert response.json() == {
        "id": connection.id,
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "type": connection.type,
        "connection_data": {
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
    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "type": "postgres",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_group_member_cannot_create_connection_with_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": -1,
            "name": "New connection",
            "description": "",
            "type": "postgres",
            "connection_data": {
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )
    assert response.status_code == 404, response.text

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_cannot_create_connection_with_unknown_group_error(
    client: AsyncClient,
    superuser: MockUser,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
):
    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "group_id": -1,
            "name": "New connection from superuser",
            "description": "",
            "type": "postgres",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )
    assert response.status_code == 404, response.text

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_guest_cannot_create_connection_error(
    client: AsyncClient,
    group: MockGroup,
):
    user = group.get_member_of_role(UserTestRoles.Guest)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "type": "postgres",
            "connection_data": {
                "type": "postgres",
                "host": "127.0.0.1",
                "port": 5432,
                "database_name": "postgres",
            },
            "auth_data": {
                "type": "basic",
                "user": "user",
                "password": "secret",
            },
        },
    )

    assert response.status_code == 403, response.text
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
