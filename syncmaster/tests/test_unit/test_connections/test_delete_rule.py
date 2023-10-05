import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, MockGroup, MockUser

from app.db.models import Acl

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_delete_rule(
    client: AsyncClient, group_connection: MockConnection
):
    acl = group_connection.acls[0]
    result = await client.delete(
        f"v1/connections/{group_connection.id}/rules/{acl.user_id}"
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_simple_user_cannot_delete_rule(
    client: AsyncClient,
    group_connection: MockConnection,
    simple_user: MockUser,
):
    acl = group_connection.acls[0]

    result = await client.delete(
        f"v1/connections/{group_connection.id}/rules/{acl.user_id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_other_group_admin_cannot_delete_rule(
    client: AsyncClient,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    acl = group_connection.acls[0]

    result = await client.delete(
        f"v1/connections/{group_connection.id}/rules/{acl.user_id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_group_member_cannot_delete_rule(
    client: AsyncClient,
    group_connection: MockConnection,
):
    member = group_connection.owner_group.members[0]
    acl = group_connection.acls[0]

    result = await client.delete(
        f"v1/connections/{group_connection.id}/rules/{acl.user_id}",
        headers={"Authorization": f"Bearer {member.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_group_admin_can_delete_rule(
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
):
    admin = group_connection.owner_group.admin
    acl = group_connection.acls[0]

    result = await client.delete(
        f"v1/connections/{group_connection.id}/rules/{acl.user_id}",
        headers={"Authorization": f"Bearer {admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Rule was deleted",
    }

    acl = (
        await session.scalars(
            select(Acl).filter_by(
                user_id=acl.user_id,
                object_id=acl.object_id,
                object_type=acl.object_type,
                rule=acl.rule,
            )
        )
    ).first()
    assert acl is None


async def test_superuser_can_delete_rule(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
    session: AsyncSession,
):
    acl = group_connection.acls[0]

    result = await client.delete(
        f"v1/connections/{group_connection.id}/rules/{acl.user_id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Rule was deleted",
    }

    acl = (
        await session.scalars(
            select(Acl).filter_by(
                user_id=acl.user_id,
                object_id=acl.object_id,
                object_type=acl.object_type,
                rule=acl.rule,
            )
        )
    ).first()
    assert acl is None


async def test_cannot_delete_rule_from_user_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    superuser: MockUser,
):
    result = await client.delete(
        f"v1/connections/{user_connection.id}/rules/{superuser.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }
