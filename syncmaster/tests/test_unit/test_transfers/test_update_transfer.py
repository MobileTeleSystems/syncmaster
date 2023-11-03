import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_unit.utils import create_connection
from tests.utils import MockGroup, MockTransfer, MockUser

pytestmark = [pytest.mark.asyncio]


async def unauthorized_user_cannot_update_connection(
    client: AsyncClient,
    user_transfer: MockTransfer,
):
    result = await client.patch(
        f"v1/transfers/{user_transfer.id}",
        json={"name": "New transfer name"},
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_simple_user_cannot_update_connection_other_user(
    client: AsyncClient, user_transfer: MockTransfer, simple_user: MockUser
):
    result = await client.patch(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"name": "New transfer name"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_user_can_update_own_transfer(
    client: AsyncClient, user_transfer: MockTransfer
):
    result = await client.patch(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {user_transfer.owner_user.token}"},
        json={"name": "New transfer name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_transfer.id,
        "user_id": user_transfer.user_id,
        "group_id": user_transfer.group_id,
        "name": "New transfer name",
        "description": user_transfer.description,
        "schedule": user_transfer.schedule,
        "is_scheduled": user_transfer.is_scheduled,
        "source_connection_id": user_transfer.source_connection_id,
        "target_connection_id": user_transfer.target_connection_id,
        "source_params": user_transfer.source_params,
        "target_params": user_transfer.target_params,
        "strategy_params": user_transfer.strategy_params,
    }


async def test_superuser_can_update_user_transfer(
    client: AsyncClient,
    user_transfer: MockTransfer,
    superuser: MockUser,
):
    result = await client.patch(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New transfer name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_transfer.id,
        "user_id": user_transfer.user_id,
        "group_id": user_transfer.group_id,
        "name": "New transfer name",
        "description": user_transfer.description,
        "schedule": user_transfer.schedule,
        "is_scheduled": user_transfer.is_scheduled,
        "source_connection_id": user_transfer.source_connection_id,
        "target_connection_id": user_transfer.target_connection_id,
        "source_params": user_transfer.source_params,
        "target_params": user_transfer.target_params,
        "strategy_params": user_transfer.strategy_params,
    }


async def test_group_admin_can_update_own_group_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    admin = group_transfer.owner_group.admin
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={"name": "New transfer name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
        "user_id": group_transfer.user_id,
        "group_id": group_transfer.group_id,
        "name": "New transfer name",
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": group_transfer.source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
    }


async def test_group_admin_cannot_update_other_group_transfer(
    client: AsyncClient,
    empty_group: MockGroup,
    group_transfer: MockTransfer,
):
    other_admin = empty_group.admin
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {other_admin.token}"},
        json={"name": "New transfer name"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_superuser_can_update_group_transfer(
    client: AsyncClient, group_transfer: MockTransfer, superuser: MockUser
):
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New transfer name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
        "user_id": group_transfer.user_id,
        "group_id": group_transfer.group_id,
        "name": "New transfer name",
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": group_transfer.source_params,
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
    }


async def test_check_connection_types_and_its_params_transfer(
    client: AsyncClient,
    user_transfer: MockTransfer,
):
    result = await client.patch(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {user_transfer.owner_user.token}"},
        json={
            "name": "New transfer name",
            "source_params": {"type": "oracle", "table_name": "New table name"},
        },
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Source connection has type `postgres` but its params has `oracle` type",
    }

    result = await client.patch(
        f"v1/transfers/{user_transfer.id}",
        headers={"Authorization": f"Bearer {user_transfer.owner_user.token}"},
        json={
            "name": "New transfer name",
            "source_params": {"type": "postgres", "table_name": "New table name"},
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": user_transfer.id,
        "user_id": user_transfer.user_id,
        "group_id": user_transfer.group_id,
        "name": "New transfer name",
        "description": user_transfer.description,
        "schedule": user_transfer.schedule,
        "is_scheduled": user_transfer.is_scheduled,
        "source_connection_id": user_transfer.source_connection_id,
        "target_connection_id": user_transfer.target_connection_id,
        "source_params": {
            "type": user_transfer.source_params["type"],
            "table_name": "New table name",
        },
        "target_params": user_transfer.target_params,
        "strategy_params": user_transfer.strategy_params,
    }


async def test_check_different_connection_owners_for_transfer(
    client: AsyncClient, group_transfer: MockTransfer, session: AsyncSession
):
    admin = group_transfer.owner_group.admin
    new_connection = await create_connection(
        session=session,
        name="New group admin connection",
        user_id=admin.id,
    )
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={"source_connection_id": new_connection.id},
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Transfer connections should belong to only one user or group",
    }

    await session.delete(new_connection)
    await session.commit()
