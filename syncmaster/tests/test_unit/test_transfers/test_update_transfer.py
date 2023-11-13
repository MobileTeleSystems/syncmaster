import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_unit.utils import create_connection
from tests.utils import MockGroup, MockTransfer, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_update_connection(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        json={"name": "New transfer name"},
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_groupless_user_cannot_update_connection(
    client: AsyncClient,
    group_transfer: MockTransfer,
    simple_user: MockUser,
):
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"name": "New transfer name"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_group_member_can_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {group_transfer.owner_group.get_member_of_role(TestUserRoles.User).token}"},
        json={"name": "New transfer name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
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


async def test_superuser_can_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
):
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"name": "New transfer name"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
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
    other_admin = empty_group.get_member_of_role("Owner")
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


async def test_check_connection_types_and_its_params_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {group_transfer.owner_group.get_member_of_role(TestUserRoles.Owner).token}"},
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
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {group_transfer.owner_group.get_member_of_role(TestUserRoles.Owner).token}"},
        json={
            "name": "New transfer name",
            "source_params": {"type": "postgres", "table_name": "New table name"},
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": group_transfer.id,
        "group_id": group_transfer.group_id,
        "name": "New transfer name",
        "description": group_transfer.description,
        "schedule": group_transfer.schedule,
        "is_scheduled": group_transfer.is_scheduled,
        "source_connection_id": group_transfer.source_connection_id,
        "target_connection_id": group_transfer.target_connection_id,
        "source_params": {
            "type": group_transfer.source_params["type"],
            "table_name": "New table name",
        },
        "target_params": group_transfer.target_params,
        "strategy_params": group_transfer.strategy_params,
    }


async def test_check_different_connection_groups_for_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
    session: AsyncSession,
):
    admin = group_transfer.owner_group.get_member_of_role("Owner")

    await client.post(
        f"v1/groups/{empty_group.id}/users/{admin.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
        json={
            "role": TestUserRoles.User,
        },
    )

    new_connection = await create_connection(
        session=session,
        name="New group admin connection",
        group_id=empty_group.id,
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
        "message": "Connections should belong to the transfer group",
    }

    await session.delete(new_connection)
    await session.commit()


async def test_user_not_in_new_connection_group_can_not_update_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    empty_group: MockGroup,
    session: AsyncSession,
):
    admin = group_transfer.owner_group.get_member_of_role("Owner")

    new_connection = await create_connection(
        session=session,
        name="New group admin connection",
        group_id=empty_group.id,
    )

    result = await client.patch(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={"source_connection_id": new_connection.id},
    )

    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }

    await session.delete(new_connection)
    await session.commit()
