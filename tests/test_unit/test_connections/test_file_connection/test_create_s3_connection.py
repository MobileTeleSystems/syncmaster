import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import AuthData, Connection
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockGroup, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.s3]


async def test_developer_plus_can_create_s3_connection(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_developer_plus)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "type": "s3",
            "connection_data": {
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

    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert response.json() == {
        "id": connection.id,
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "type": connection.type,
        "connection_data": {
            "host": connection.data["host"],
            "bucket": connection.data["bucket"],
            "port": connection.data["port"],
            "region": connection.data["region"],
            "protocol": connection.data["protocol"],
            "bucket_style": connection.data["bucket_style"],
            "additional_params": connection.data["additional_params"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "access_key": decrypted["access_key"],
        },
    }


@pytest.mark.parametrize(["port", "protocol"], [(80, "http"), (443, "https")])
async def test_developer_plus_can_create_s3_connection_auto_generate_port(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
    protocol: str,
    port: int,
):
    user = group.get_member_of_role(role_developer_plus)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "type": "s3",
            "connection_data": {
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

    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert response.json() == {
        "id": connection.id,
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "type": connection.type,
        "connection_data": {
            "host": connection.data["host"],
            "bucket": connection.data["bucket"],
            "port": port,
            "region": connection.data["region"],
            "protocol": connection.data["protocol"],
            "bucket_style": connection.data["bucket_style"],
            "additional_params": connection.data["additional_params"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "access_key": decrypted["access_key"],
        },
    }
