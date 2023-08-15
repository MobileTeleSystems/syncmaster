import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import UserGroup
from tests.utils import MockGroup, MockTransfer, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_read_connection(
    client: AsyncClient, user_transfer: MockTransfer
):
    result = await client.get(f"v1/transfers/{user_transfer.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_owner_can_read_transfer_of_self(
    client: AsyncClient, user_transfer: MockTransfer, simple_user: MockUser
):
    result = await client.get(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }

    result = await client.get(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {user_transfer.owner_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_transfer.id,
        "user_id": user_transfer.user_id,
        "group_id": user_transfer.group_id,
        "name": user_transfer.name,
        "description": user_transfer.description,
        "schedule": user_transfer.schedule,
        "is_scheduled": user_transfer.is_scheduled,
        "source_connection_id": user_transfer.source_connection_id,
        "target_connection_id": user_transfer.target_connection_id,
        "source_params": user_transfer.source_params,
        "target_params": user_transfer.target_params,
        "strategy_params": user_transfer.strategy_params,
    }


async def test_group_admin_can_read_transfer_of_his_group(
    client: AsyncClient, group_transfer: MockTransfer, simple_user: MockUser
):
    result = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }

    result = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {group_transfer.owner_group.admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
        "user_id": group_transfer.user_id,
        "group_id": group_transfer.group_id,
        "name": group_transfer.name,
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": group_transfer.source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
    }


async def test_group_admin_cannot_read_transfer_of_other(
    client: AsyncClient,
    group_transfer: MockTransfer,
    user_transfer: MockTransfer,
    empty_group: MockGroup,
):
    for transfer in group_transfer, user_transfer:
        result = await client.get(
            f"v1/transfers/{transfer.id}",
            headers={"Authorization": f"Bearer {empty_group.admin.token}"},
        )
        assert result.status_code == 404
        assert result.json() == {
            "ok": False,
            "status_code": 404,
            "message": "Transfer not found",
        }


async def test_group_member_without_acl_can_read_transfer_of_group(
    client: AsyncClient, group_transfer: MockTransfer, session: AsyncSession
):
    group = group_transfer.owner_group
    group_member = group_transfer.owner_group.members[0]

    result = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {group_member.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
        "user_id": group_transfer.user_id,
        "group_id": group_transfer.group_id,
        "name": group_transfer.name,
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": group_transfer.source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
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
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {group_member.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_superuser_can_read_all_transfers(
    client: AsyncClient,
    superuser: MockUser,
    user_transfer: MockTransfer,
    group_transfer: MockTransfer,
):
    result = await client.get(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_transfer.id,
        "user_id": user_transfer.user_id,
        "group_id": user_transfer.group_id,
        "name": user_transfer.name,
        "description": user_transfer.description,
        "schedule": user_transfer.schedule,
        "is_scheduled": user_transfer.is_scheduled,
        "source_connection_id": user_transfer.source_connection_id,
        "target_connection_id": user_transfer.target_connection_id,
        "source_params": user_transfer.source_params,
        "target_params": user_transfer.target_params,
        "strategy_params": user_transfer.strategy_params,
    }

    result = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
        "user_id": group_transfer.user_id,
        "group_id": group_transfer.group_id,
        "name": group_transfer.name,
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": group_transfer.source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
    }

    result = await client.get(
        f"v1/transfers/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
