# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import pytest
from backend.config import Settings
from db import AuthData, Connection
from db.repositories import decrypt_auth_data
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from tests.utils import MockGroup, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend, pytest.mark.s3]


async def test_developer_plus_can_create_s3_connection(
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
                "type": "s3",
                "bucket": "some_bucket",
                "host": "some_host",
                "port": 80,
                "region": "some_region",
                "protocol": "http",
                "bucket_style": "domain",
            },
            "auth_data": {
                "type": "s3",
                "access_key": "access_key",
                "secret_key": "secret_key",
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
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "connection_data": {
            "type": connection.data["type"],
            "host": connection.data["host"],
            "bucket": connection.data["bucket"],
            "port": connection.data["port"],
            "region": connection.data["region"],
            "protocol": connection.data["protocol"],
            "bucket_style": connection.data["bucket_style"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "access_key": decrypted["access_key"],
        },
    }


@pytest.mark.parametrize("port,protocol", [(80, "http"), (443, "https")])
async def test_developer_plus_can_create_s3_connection_auto_generate_port(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
    protocol: str,
    port: int,
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
                "type": "s3",
                "bucket": "some_bucket",
                "host": "some_host",
                "region": "some_region",
                "protocol": protocol,
                "bucket_style": "domain",
            },
            "auth_data": {
                "type": "s3",
                "access_key": "access_key",
                "secret_key": "secret_key",
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
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "connection_data": {
            "type": connection.data["type"],
            "host": connection.data["host"],
            "bucket": connection.data["bucket"],
            "port": port,
            "region": connection.data["region"],
            "protocol": connection.data["protocol"],
            "bucket_style": connection.data["bucket_style"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "access_key": decrypted["access_key"],
        },
    }
