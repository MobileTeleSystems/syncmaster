import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockUser

from app.db.models import Acl, Connection, ObjectType, Rule

pytestmark = [pytest.mark.asyncio]


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


async def test_simple_user_can_create_connection(
    client: AsyncClient, simple_user: MockUser, session: AsyncSession
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
            "type": connection.auth_data["type"],
            "user": connection.auth_data["user"],
        },
    }
    # check that acl not created for user on own connection
    acl = (
        await session.scalars(
            select(Acl).filter_by(
                user_id=simple_user.id,
                object_id=connection.id,
                object_type=ObjectType.CONNECTION,
            )
        )
    ).first()
    assert acl is None


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
            "type": connection.auth_data["type"],
            "user": connection.auth_data["user"],
        },
    }
    acl = (
        await session.scalars(
            select(Acl).filter_by(
                user_id=member.id,
                object_id=connection.id,
                object_type=ObjectType.CONNECTION,
            )
        )
    ).first()
    assert acl is not None
    assert acl.rule == Rule.DELETE


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
            "type": connection.auth_data["type"],
            "user": connection.auth_data["user"],
        },
    }
    # check that acl not created for superuser
    acl = (
        await session.scalars(
            select(Acl).filter_by(
                user_id=admin.id,
                object_id=connection.id,
                object_type=ObjectType.CONNECTION,
            )
        )
    ).first()
    assert acl is None


async def test_superuser_can_create_group_connection(
    client: AsyncClient,
    superuser: MockUser,
    empty_group: MockGroup,
    not_empty_group: MockGroup,
    session: AsyncSession,
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
                "type": connection.auth_data["type"],
                "user": connection.auth_data["user"],
            },
        }

        # check that acl not created for superuser
        acl = (
            await session.scalars(
                select(Acl).filter_by(
                    user_id=superuser.id,
                    object_id=connection.id,
                    object_type=ObjectType.CONNECTION,
                )
            )
        ).first()
        assert acl is None


async def test_superuser_can_create_other_user_connection(
    client: AsyncClient,
    superuser: MockUser,
    simple_user: MockUser,
    session: AsyncSession,
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
            "type": connection.auth_data["type"],
            "user": connection.auth_data["user"],
        },
    }
