import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockUser

from app.db.models import Connection

pytestmark = [pytest.mark.asyncio]


async def test_create_oracle_connection_with_service_name(
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
                "type": "oracle",
                "host": "127.0.0.1",
                "port": 1521,
                "service_name": "service_name",
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
            "additional_params": connection.data["additional_params"],
            "service_name": connection.data["service_name"],
            "sid": connection.data["sid"],
        },
        "auth_data": {
            "type": connection.auth_data["type"],
            "user": connection.auth_data["user"],
        },
    }


async def test_create_oracle_connection_with_sid(
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
            "sid": connection.data["sid"],
            "service_name": connection.data["service_name"],
            "additional_params": connection.data["additional_params"],
        },
        "auth_data": {
            "type": connection.auth_data["type"],
            "user": connection.auth_data["user"],
        },
    }


async def test_create_oracle_connection_with_sid_and_service_name_error(
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

    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "loc": [
                    "body",
                    "connection_data",
                    "CreateOracleConnectionSchema",
                    "__root__",
                ],
                "msg": "You must specify either sid or service_name but not both",
                "type": "value_error",
            }
        ]
    }
