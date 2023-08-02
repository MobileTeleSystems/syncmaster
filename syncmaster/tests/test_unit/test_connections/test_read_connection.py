import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserGroup
from tests.utils import MockConnection, MockGroup, MockUser


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_read_connection(
    client: AsyncClient, user_connection: MockConnection
):
    result = await client.get(f"v1/connections/{user_connection.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


@pytest.mark.asyncio
async def test_owner_can_read_connection_of_self(
    client: AsyncClient, user_connection: MockConnection, simple_user: MockUser
):
    result = await client.get(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }

    result = await client.get(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {user_connection.owner_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_connection.id,
        "description": user_connection.description,
        "group_id": user_connection.group_id,
        "user_id": user_connection.user_id,
        "name": user_connection.name,
        "connection_data": {
            "type": user_connection.data["type"],
            "database_name": user_connection.data["database_name"],
            "host": user_connection.data["host"],
            "port": user_connection.data["port"],
            "user": user_connection.data["user"],
            "additional_params": user_connection.data["additional_params"],
        },
    }


@pytest.mark.asyncio
async def test_group_admin_can_read_connection_of_his_group(
    client: AsyncClient, group_connection: MockConnection, simple_user: MockUser
):
    result = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }

    result = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {group_connection.owner_group.admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "user_id": group_connection.user_id,
        "name": group_connection.name,
        "connection_data": {
            "type": group_connection.data["type"],
            "database_name": group_connection.data["database_name"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "user": group_connection.data["user"],
            "additional_params": group_connection.data["additional_params"],
        },
    }


@pytest.mark.asyncio
async def test_group_admin_cannot_read_connection_of_other(
    client: AsyncClient,
    group_connection: MockConnection,
    user_connection: MockConnection,
    empty_group: MockGroup,
):
    for connection in group_connection, user_connection:
        result = await client.get(
            f"v1/connections/{connection.id}",
            headers={"Authorization": f"Bearer {empty_group.admin.token}"},
        )
        assert result.status_code == 404
        assert result.json() == {
            "ok": False,
            "status_code": 404,
            "message": "Connection not found",
        }


@pytest.mark.asyncio
async def test_group_member_without_acl_cann_read_connection_of_group(
    client: AsyncClient, group_connection: MockConnection, session: AsyncSession
):
    group = group_connection.owner_group
    group_member = group_connection.owner_group.members[0]

    result = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {group_member.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "user_id": group_connection.user_id,
        "name": group_connection.name,
        "connection_data": {
            "type": group_connection.data["type"],
            "database_name": group_connection.data["database_name"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "user": group_connection.data["user"],
            "additional_params": group_connection.data["additional_params"],
        },
    }

    # check after delete from group
    ug = (
        await session.scalars(
            select(UserGroup).where(
                UserGroup.group_id == group.id, UserGroup.user_id == group_member.id
            )
        )
    ).one()

    await session.delete(ug)
    await session.commit()

    result = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {group_member.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


@pytest.mark.asyncio
async def test_superuser_can_read_all_connections(
    client: AsyncClient,
    superuser: MockUser,
    user_connection: MockConnection,
    group_connection: MockConnection,
):
    result = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "user_id": group_connection.user_id,
        "name": group_connection.name,
        "connection_data": {
            "type": group_connection.data["type"],
            "database_name": group_connection.data["database_name"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "user": group_connection.data["user"],
            "additional_params": group_connection.data["additional_params"],
        },
    }

    result = await client.get(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_connection.id,
        "description": user_connection.description,
        "group_id": user_connection.group_id,
        "user_id": user_connection.user_id,
        "name": user_connection.name,
        "connection_data": {
            "type": user_connection.data["type"],
            "database_name": user_connection.data["database_name"],
            "host": user_connection.data["host"],
            "port": user_connection.data["port"],
            "user": user_connection.data["user"],
            "additional_params": user_connection.data["additional_params"],
        },
    }

    result = await client.get(
        f"v1/connections/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }
