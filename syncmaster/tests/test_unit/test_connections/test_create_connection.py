import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockUser

from app.config import Settings
from app.db.models import AuthData, Connection
from app.db.repositories.utils import decrypt_auth_data

pytestmark = [pytest.mark.asyncio]


async def test_simple_user_can_create_connection(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    settings: Settings,
    event_loop,
    request,
):
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "user_id": simple_user.id,
            "group_id": None,
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
                user_id=simple_user.id,
            )
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            )
        )
    ).one()

    def delete_rows():
        async def afin():
            await session.delete(creds)
            await session.delete(connection)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    assert result.status_code == 200
    assert result.json() == {
        "id": connection.id,
        "name": connection.name,
        "description": connection.description,
        "group_id": connection.group_id,
        "user_id": connection.user_id,
        "connection_data": {
            "type": connection.data["type"],
            "host": connection.data["host"],
            "port": connection.data["port"],
            "database_name": connection.data["database_name"],
            "additional_params": connection.data["additional_params"],
        },
        "auth_data": {
            "type": decrypt_auth_data(creds.value, settings=settings)["type"],
            "user": decrypt_auth_data(creds.value, settings=settings)["user"],
        },
    }


async def test_unauthorized_user_cannot_create_connection(client: AsyncClient):
    result = await client.post(
        "v1/connections",
        json={
            "user_id": 1,
            "group_id": None,
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


async def test_user_cannot_create_connection_to_other_user(
    client: AsyncClient,
    simple_user: MockUser,
    superuser: MockUser,
):
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "user_id": superuser.id,
            "group_id": None,
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
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_check_fields_validation_on_create_connection(
    client: AsyncClient, simple_user: MockUser
):
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "user_id": simple_user.id,
            "group_id": None,
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
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "loc": ["body", "name"],
                "msg": "none is not an allowed value",
                "type": "type_error.none.not_allowed",
            }
        ]
    }

    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "user_id": simple_user.id,
            "group_id": None,
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
                "loc": ["body", "description"],
                "msg": "none is not an allowed value",
                "type": "type_error.none.not_allowed",
            }
        ]
    }

    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "user_id": None,
            "group_id": None,
            "name": "Name",
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
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "loc": ["body", "__root__"],
                "msg": "Connection must have one owner: group or user",
                "type": "value_error",
            },
        ]
    }

    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "user_id": simple_user.id,
            "group_id": None,
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
                "loc": ["body", "connection_data"],
                "msg": "No match for discriminator 'type' and value 'POSTGRESQL' (allowed values: 'hive', 'oracle', 'postgres')",
                "type": "value_error.discriminated_union.invalid_discriminator",
                "ctx": {
                    "discriminator_key": "type",
                    "discriminator_value": "POSTGRESQL",
                    "allowed_values": "'hive', 'oracle', 'postgres'",
                },
            }
        ]
    }


async def test_simple_user_cannot_create_group_connection(
    client: AsyncClient, simple_user: MockUser, empty_group: MockGroup
):
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "user_id": None,
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
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_group_member_can_create_group_connection(
    client: AsyncClient,
    not_empty_group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    event_loop,
    request,
):
    member = not_empty_group.members[0]
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {member.token}"},
        json={
            "user_id": None,
            "group_id": not_empty_group.id,
            "name": "Member connection",
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
                name="Member connection",
                group_id=not_empty_group.id,
            )
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            )
        )
    ).one()

    def delete_rows():
        async def afin():
            await session.delete(creds)
            await session.delete(connection)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    assert result.status_code == 200
    assert result.json() == {
        "id": connection.id,
        "user_id": connection.user_id,
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
            "type": decrypt_auth_data(creds.value, settings=settings)["type"],
            "user": decrypt_auth_data(creds.value, settings=settings)["user"],
        },
    }


async def test_other_group_admin_cannot_create_group_connection(
    client: AsyncClient, empty_group: MockGroup, not_empty_group: MockGroup
):
    admin = empty_group.admin
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={
            "user_id": None,
            "group_id": not_empty_group.id,
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
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_group_admin_can_create_group_connection(
    client: AsyncClient,
    empty_group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    event_loop,
    request,
):
    admin = empty_group.admin
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={
            "user_id": None,
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
    connection = (
        await session.scalars(
            select(Connection).filter_by(
                name="New connection",
                group_id=empty_group.id,
            )
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            )
        )
    ).one()

    def delete_rows():
        async def afin():
            await session.delete(creds)
            await session.delete(connection)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    assert result.status_code == 200
    assert result.json() == {
        "id": connection.id,
        "user_id": connection.user_id,
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
            "type": decrypt_auth_data(creds.value, settings=settings)["type"],
            "user": decrypt_auth_data(creds.value, settings=settings)["user"],
        },
    }


async def test_superuser_can_create_group_connection(
    client: AsyncClient,
    superuser: MockUser,
    empty_group: MockGroup,
    not_empty_group: MockGroup,
    session: AsyncSession,
    settings: Settings,
):
    for group in empty_group, not_empty_group:
        result = await client.post(
            "v1/connections",
            headers={"Authorization": f"Bearer {superuser.token}"},
            json={
                "user_id": None,
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
                )
            )
        ).first()

        creds = (
            await session.scalars(
                select(AuthData).filter_by(
                    connection_id=connection.id,
                )
            )
        ).one()

        assert result.status_code == 200
        assert result.json() == {
            "id": connection.id,
            "user_id": connection.user_id,
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
                "type": decrypt_auth_data(creds.value, settings=settings)["type"],
                "user": decrypt_auth_data(creds.value, settings=settings)["user"],
            },
        }


async def test_superuser_can_create_other_user_connection(
    client: AsyncClient,
    superuser: MockUser,
    simple_user: MockUser,
    session: AsyncSession,
    settings: Settings,
    event_loop,
    request,
):
    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "user_id": simple_user.id,
            "group_id": None,
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
                user_id=simple_user.id,
            )
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            )
        )
    ).one()

    def delete_rows():
        async def afin():
            await session.delete(creds)
            await session.delete(connection)
            await session.commit()

        event_loop.run_until_complete(afin())

    request.addfinalizer(delete_rows)

    assert result.status_code == 200
    assert result.json() == {
        "id": connection.id,
        "user_id": connection.user_id,
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
            "type": decrypt_auth_data(creds.value, settings=settings)["type"],
            "user": decrypt_auth_data(creds.value, settings=settings)["user"],
        },
    }
