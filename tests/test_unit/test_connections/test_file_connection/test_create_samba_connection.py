import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import AuthData, Connection
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockGroup, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.samba]


async def test_developer_plus_can_create_samba_connection(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_developer_plus)

    result = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "type": "samba",
            "connection_data": {
                "host": "some_host",
                "port": 80,
                "share": "some_folder",
                "protocol": "SMB",
            },
            "auth_data": {
                "type": "samba",
                "auth_type": "NTLMv2",
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

    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert result.status_code == 200, result.json()
    assert result.json() == {
        "id": connection.id,
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "type": connection.type,
        "connection_data": {
            "host": connection.data["host"],
            "port": connection.data["port"],
            "share": connection.data["share"],
            "protocol": connection.data["protocol"],
            "domain": "",
        },
        "auth_data": {
            "type": decrypted["type"],
            "auth_type": decrypted["auth_type"],
            "user": decrypted["user"],
        },
    }
