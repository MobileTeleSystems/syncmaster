import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import AuthData, Connection
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.settings import Settings
from tests.mocks import MockGroup, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend, pytest.mark.clickhouse]


async def test_developer_plus_can_create_clickhouse_connection(
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
                "type": "clickhouse",
                "host": "127.0.0.1",
                "port": 8123,
                "database": "database_name",
            },
            "auth_data": {
                "type": "clickhouse",
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
            "database": connection.data["database"],
            "additional_params": connection.data["additional_params"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "user": decrypted["user"],
        },
    }
