import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Acl, ObjectType, Rule
from tests.utils import MockConnection, MockGroup, MockUser


@pytest.mark.asyncio
async def test_unauthorized_user_cannot_delete_connection(
    client: AsyncClient, user_connection: MockConnection
):
    result = await client.delete(
        f"v1/connections/{user_connection.id}",
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


@pytest.mark.asyncio
async def test_simple_user_cannot_delete_connection_other_user(
    client: AsyncClient, user_connection: MockConnection, simple_user: MockUser
):
    result = await client.delete(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


@pytest.mark.asyncio
async def test_user_can_delete_own_connection(
    client: AsyncClient, user_connection: MockConnection, session: AsyncSession
):
    result = await client.delete(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {user_connection.owner_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was deleted",
    }
    await session.refresh(user_connection.connection)
    assert user_connection.connection.is_deleted

    result = await client.delete(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {user_connection.owner_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


@pytest.mark.asyncio
async def test_superuser_can_delete_user_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    superuser: MockUser,
    session: AsyncSession,
):
    result = await client.delete(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was deleted",
    }
    await session.refresh(user_connection.connection)
    assert user_connection.connection.is_deleted

    # try delete twice
    result = await client.delete(
        f"v1/connections/{user_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "rule",
    (None, Rule.WRITE),
)
async def test_member_cannot_delete_connection_without_delete_rule(
    rule: Rule | None,
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
):
    member = group_connection.owner_group.members[0]
    if rule is not None:
        acl = Acl(
            object_id=group_connection.id,
            object_type=ObjectType.CONNECTION,
            user_id=member.id,
            rule=rule,
        )
        session.add(acl)
        await session.commit()

    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {member.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


@pytest.mark.asyncio
async def test_member_can_delete_connection_with_delete_rule(
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
):
    member = group_connection.owner_group.members[0]
    acl = Acl(
        object_id=group_connection.id,
        object_type=ObjectType.CONNECTION,
        user_id=member.id,
        rule=Rule.DELETE,
    )
    session.add(acl)
    await session.commit()

    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {member.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was deleted",
    }

    await session.delete(acl)
    await session.commit()


@pytest.mark.asyncio
async def test_group_admin_can_delete_own_group_connection(
    client: AsyncClient, group_connection: MockConnection
):
    admin = group_connection.owner_group.admin
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was deleted",
    }


@pytest.mark.asyncio
async def test_group_admin_cannot_delete_other_group_connection(
    client: AsyncClient, empty_group: MockGroup, group_connection: MockConnection
):
    other_admin = empty_group.admin
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {other_admin.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


@pytest.mark.asyncio
async def test_superuser_can_delete_group_connection(
    client: AsyncClient, group_connection: MockConnection, superuser: MockUser
):
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was deleted",
    }
