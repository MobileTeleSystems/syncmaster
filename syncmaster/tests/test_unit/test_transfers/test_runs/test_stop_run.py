import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockRun, MockUser, TestUserRoles

from app.db.models import Status

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_stop_run(
    client: AsyncClient,
    group_run: MockRun,
) -> None:
    result = await client.post(f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}/stop")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_groupless_user_can_not_stop_run(
    client: AsyncClient,
    simple_user: MockUser,
    group_run: MockRun,
    session: AsyncSession,
) -> None:
    result = await client.post(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }


async def test_group_admin_can_stop_run_of_transfer_his_group(
    client: AsyncClient,
    simple_user: MockUser,
    group_run: MockRun,
    session: AsyncSession,
) -> None:
    result = await client.post(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }

    result = await client.post(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}/stop",
        headers={
            "Authorization": f"Bearer {group_run.transfer.owner_group.get_member_of_role(TestUserRoles.Owner).token}"
        },
    )

    await session.refresh(group_run.run)
    assert group_run.status == Status.SEND_STOP_SIGNAL

    assert result.status_code == 200
    assert result.json() == {
        "id": group_run.id,
        "transfer_id": group_run.transfer_id,
        "status": group_run.status.value,
        "log_url": group_run.log_url,
        "started_at": group_run.started_at,
        "ended_at": group_run.ended_at,
        "transfer_dump": group_run.transfer_dump,
    }


async def test_other_group_admin_cannot_stop_run_of_other_group_transfer(
    client: AsyncClient,
    group_run: MockRun,
    empty_group: MockGroup,
    session: AsyncSession,
) -> None:
    result = await client.post(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
    await session.refresh(group_run.run)
    assert group_run.status != Status.SEND_STOP_SIGNAL


async def test_superuser_can_stop_run(
    client: AsyncClient,
    superuser: MockUser,
    group_run: MockRun,
    session: AsyncSession,
) -> None:
    result = await client.post(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    await session.refresh(group_run.run)
    assert group_run.status == Status.SEND_STOP_SIGNAL

    assert result.status_code == 200
    assert result.json() == {
        "id": group_run.id,
        "transfer_id": group_run.transfer_id,
        "status": group_run.status.value,
        "log_url": group_run.log_url,
        "started_at": group_run.started_at,
        "ended_at": group_run.ended_at,
        "transfer_dump": group_run.transfer_dump,
    }


@pytest.mark.parametrize("status", (Status.SEND_STOP_SIGNAL, Status.FINISHED, Status.FAILED, Status.STOPPED))
async def test_cannot_stop_run_in_status_except_started_created(
    status: Status,
    client: AsyncClient,
    group_run: MockRun,
    session: AsyncSession,
) -> None:
    group_run.run.status = status
    session.add(group_run.run)
    await session.commit()

    result = await client.post(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}/stop",
        headers={
            "Authorization": f"Bearer {group_run.transfer.owner_group.get_member_of_role(TestUserRoles.Owner).token}"
        },
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": f"Cannot stop run {group_run.id}. Current status is {group_run.status}",
    }
