import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockUser

from app.config import Settings
from app.db.models import AuthData, Connection
from app.db.repositories.utils import decrypt_auth_data

pytestmark = [pytest.mark.asyncio]


async def test_create_hive_connection(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    settings: Settings,
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
                "type": "hive",
                "cluster": "cluster",
            },
            "auth_data": {
                "type": "hive",
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

    assert result.status_code == 200
    assert result.json() == {
        "id": connection.id,
        "user_id": connection.user_id,
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "connection_data": {
            "type": connection.data["type"],
            "cluster": connection.data["cluster"],
            "additional_params": connection.data["additional_params"],
        },
        "auth_data": {
            "type": decrypt_auth_data(creds.value, settings=settings)["type"],
            "user": decrypt_auth_data(creds.value, settings=settings)["user"],
        },
    }
