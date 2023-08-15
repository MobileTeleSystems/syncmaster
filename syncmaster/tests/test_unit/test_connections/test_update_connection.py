import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Acl, ObjectType, Rule
from tests.utils import MockConnection, MockGroup, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_update_connection(
    client: AsyncClient, user_connection: MockConnection
):
    result = await client.patch(
        f"v1/connections/{user_connection.id}", json={"name": "New connection name"}
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_simple_user_cannot_update_connection_other_user(
    client: AsyncClient, user_connection: MockConnection, simple_user: MockUser
):
    result = await client.patch(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_user_can_update_own_connection(
    client: AsyncClient, user_connection: MockConnection
):
    result = await client.patch(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {user_connection.owner_user.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_connection.id,
        "name": "New connection name",
        "description": user_connection.description,
        "user_id": user_connection.user_id,
        "group_id": user_connection.group_id,
        "connection_data": {
            "type": user_connection.data["type"],
            "host": user_connection.data["host"],
            "port": user_connection.data["port"],
            "user": user_connection.data["user"],
            "additional_params": user_connection.data["additional_params"],
            "database_name": user_connection.data["database_name"],
        },
    }


async def test_superuser_can_update_user_connection(
    client: AsyncClient, user_connection: MockConnection, superuser: MockUser
):
    result = await client.patch(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_connection.id,
        "name": "New connection name",
        "description": user_connection.description,
        "user_id": user_connection.user_id,
        "group_id": user_connection.group_id,
        "connection_data": {
            "type": user_connection.data["type"],
            "host": user_connection.data["host"],
            "port": user_connection.data["port"],
            "user": user_connection.data["user"],
            "additional_params": user_connection.data["additional_params"],
            "database_name": user_connection.data["database_name"],
        },
    }


@pytest.mark.parametrize("rule", (Rule.WRITE, Rule.DELETE))
async def test_member_can_update_connection_with_write_or_delete_rule(
    rule: Rule,
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
):
    member = group_connection.owner_group.members[0]
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {member.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }

    acl = Acl(
        object_id=group_connection.id,
        object_type=ObjectType.CONNECTION,
        user_id=member.id,
        rule=rule,
    )
    session.add(acl)
    await session.commit()

    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {member.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": "New connection name",
        "description": group_connection.description,
        "user_id": group_connection.user_id,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "user": group_connection.data["user"],
            "additional_params": group_connection.data["additional_params"],
            "database_name": group_connection.data["database_name"],
        },
    }

    await session.delete(acl)
    await session.commit()


async def test_group_admin_can_update_own_group_connection(
    client: AsyncClient, group_connection: MockConnection
):
    admin = group_connection.owner_group.admin
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": "New connection name",
        "description": group_connection.description,
        "user_id": group_connection.user_id,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "user": group_connection.data["user"],
            "additional_params": group_connection.data["additional_params"],
            "database_name": group_connection.data["database_name"],
        },
    }


async def test_group_admin_cannot_update_other_group_connection(
    client: AsyncClient, empty_group: MockGroup, group_connection: MockConnection
):
    other_admin = empty_group.admin
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {other_admin.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_superuser_can_update_group_connection(
    client: AsyncClient, group_connection: MockConnection, superuser: MockUser
):
    result = await client.patch(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New connection name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_connection.id,
        "name": "New connection name",
        "description": group_connection.description,
        "user_id": group_connection.user_id,
        "group_id": group_connection.group_id,
        "connection_data": {
            "type": group_connection.data["type"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "user": group_connection.data["user"],
            "additional_params": group_connection.data["additional_params"],
            "database_name": group_connection.data["database_name"],
        },
    }


async def test_can_update_connection_data_fields(
    client: AsyncClient,
    user_connection: MockConnection,
):
    result = await client.patch(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {user_connection.owner_user.token}"},
        json={"connection_data": {"host": "localhost"}},
    )
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "loc": ["body", "connection_data"],
                "msg": "Discriminator 'type' is missing in value",
                "type": "value_error.discriminated_union.missing_discriminator",
                "ctx": {"discriminator_key": "type"},
            }
        ]
    }

    result = await client.patch(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {user_connection.owner_user.token}"},
        json={"connection_data": {"type": "postgres", "host": "localhost"}},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_connection.id,
        "name": user_connection.name,
        "description": user_connection.description,
        "user_id": user_connection.user_id,
        "group_id": user_connection.group_id,
        "connection_data": {
            "type": user_connection.data["type"],
            "host": "localhost",
            "port": user_connection.data["port"],
            "user": user_connection.data["user"],
            "additional_params": user_connection.data["additional_params"],
            "database_name": user_connection.data["database_name"],
        },
    }
