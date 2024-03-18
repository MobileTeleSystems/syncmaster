# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.config import Settings
from syncmaster.db import AuthData, Connection
from syncmaster.db.repositories import decrypt_auth_data
from tests.utils import MockGroup, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend, pytest.mark.oracle]


async def test_developer_plus_can_create_oracle_connection_with_service_name(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
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

    # Assert
    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert result.status_code == 200
    assert result.json() == {
        "id": connection.id,
        "name": connection.name,
        "description": connection.description,
        "group_id": connection.group_id,
        "connection_data": {
            "type": connection.data["type"],
            "host": connection.data["host"],
            "port": connection.data["port"],
            "additional_params": connection.data["additional_params"],
            "service_name": connection.data["service_name"],
            "sid": connection.data["sid"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "user": decrypted["user"],
        },
    }


async def test_developer_plus_can_create_oracle_connection_with_sid(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
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

    # Assert
    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert result.status_code == 200
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


async def test_developer_plus_create_oracle_connection_with_sid_and_service_name_error(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    role_developer_plus: UserTestRoles,
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
