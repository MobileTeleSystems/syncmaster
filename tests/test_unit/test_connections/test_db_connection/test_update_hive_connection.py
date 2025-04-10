import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import AuthData
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockConnection, UserTestRoles
from tests.test_unit.utils import fetch_connection_json

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.hive]


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "hive",
            {
                "cluster": "cluster",
            },
            None,
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_hive_connection_no_credentials(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "connection_data": {"cluster": "new_cluster"}},
    )

    assert result.status_code == 200, result.json()
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.connection.name,
        "description": group_connection.description,
        "type": group_connection.type,
        "group_id": group_connection.group_id,
        "connection_data": {"cluster": "new_cluster"},
        "auth_data": None,
    }


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "hive",
            {
                "cluster": "cluster",
            },
            None,
        ),
        (
            "hive",
            {
                "cluster": "cluster",
            },
            {
                "type": "basic",
                "user": "user",
                "password": "password",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
@pytest.mark.parametrize(
    "new_auth_data",
    [
        None,
        {
            "type": "basic",
            "user": "user",
            "password": "password",
        },
    ],
)
async def test_developer_plus_can_update_hive_connection_replace_credentials_full(
    client: AsyncClient,
    session: AsyncSession,
    settings: Settings,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
    new_auth_data: dict | None,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "auth_data": new_auth_data},
    )

    expected_auth_data = (
        {
            "type": new_auth_data["type"],
            "user": new_auth_data["user"],
        }
        if new_auth_data
        else None
    )

    assert result.status_code == 200, result.json()
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.connection.name,
        "description": group_connection.description,
        "type": group_connection.type,
        "group_id": group_connection.group_id,
        "connection_data": group_connection.connection.data,
        "auth_data": expected_auth_data,
    }

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=group_connection.id,
            ),
        )
    ).one_or_none()
    if new_auth_data:
        decrypted = decrypt_auth_data(creds.value, settings=settings)
        assert decrypted == new_auth_data
    else:
        assert not creds


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "hive",
            {
                "cluster": "cluster",
            },
            {
                "type": "basic",
                "user": "user",
                "password": "password",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_hive_connection_replace_credentials_partial(
    client: AsyncClient,
    session: AsyncSession,
    settings: Settings,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    new_auth_data = {
        "type": "basic",
        "user": "user",
        # no password
    }
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "auth_data": new_auth_data},
    )

    assert result.status_code == 200, result.json()
    assert result.json() == {
        "id": group_connection.id,
        "name": group_connection.connection.name,
        "description": group_connection.description,
        "type": group_connection.type,
        "group_id": group_connection.group_id,
        "connection_data": group_connection.connection.data,
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=group_connection.id,
            ),
        )
    ).one()
    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert decrypted == {"type": "basic", "user": "user", "password": "password"}


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "hive",
            {
                "cluster": "cluster",
            },
            None,
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_hive_connection_missing_credentials(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    new_auth_data = {
        "type": "basic",
        "user": "user",
    }
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    result = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={**connection_json, "auth_data": new_auth_data},
    )

    assert result.status_code == 409, result.json()
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "You cannot update the connection auth type without providing a new secret value.",
            "details": None,
        },
    }
