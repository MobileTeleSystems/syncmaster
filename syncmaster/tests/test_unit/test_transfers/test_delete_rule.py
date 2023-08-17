import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Acl
from tests.utils import MockGroup, MockTransfer, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_delete_rule(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    acl = group_transfer.acls[0]
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}/rules/{acl.user_id}",
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_simple_user_cannot_delete_rule(
    client: AsyncClient,
    group_transfer: MockTransfer,
    simple_user: MockUser,
):
    acl = group_transfer.acls[0]
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}/rules/{acl.user_id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_other_group_admin_cannot_delete_transfer_rule(
    client: AsyncClient,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
):
    acl = group_transfer.acls[0]
    result = await client.delete(
        f"v1/transfers/{group_transfer.id}/rules/{acl.user_id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_group_member_cannot_delete_transfer_rule(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    member = group_transfer.owner_group.members[1]
    acl = group_transfer.acls[0]

    result = await client.delete(
        f"v1/transfers/{group_transfer.id}/rules/{acl.user_id}",
        headers={"Authorization": f"Bearer {member.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_group_admin_can_delete_transfer_rule(
    client: AsyncClient, group_transfer: MockTransfer, session: AsyncSession
):
    admin = group_transfer.owner_group.admin
    acl = group_transfer.acls[0]

    result = await client.delete(
        f"v1/transfers/{group_transfer.id}/rules/{acl.user_id}",
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


async def test_superuser_can_delete_transfer_rule(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
    session: AsyncSession,
):
    acl = group_transfer.acls[0]

    result = await client.delete(
        f"v1/transfers/{group_transfer.id}/rules/{acl.user_id}",
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


async def test_cannot_delete_rule_from_user_transfer(
    client: AsyncClient,
    user_transfer: MockTransfer,
    superuser: MockUser,
):
    result = await client.delete(
        f"v1/transfers/{user_transfer.id}/rules/{superuser.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }
