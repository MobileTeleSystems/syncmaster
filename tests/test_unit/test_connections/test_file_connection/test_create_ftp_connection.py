import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import AuthData, Connection
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockGroup, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.ftp]


async def test_developer_plus_can_create_ftp_connection(
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
            "type": "ftp",
            "connection_data": {
                "host": "some_host",
                "port": 80,
            },
            "auth_data": {
                "type": "basic",
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
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "type": connection.type,
        "connection_data": {
            "host": connection.data["host"],
            "port": connection.data["port"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "user": decrypted["user"],
        },
    }
