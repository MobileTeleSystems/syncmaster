import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockRun, MockUser

from app.db.models import Status

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_stop_run(
    client: AsyncClient,
    user_run: MockRun,
) -> None:
    result = await client.post(
        f"v1/transfers/{user_run.transfer.id}/runs/{user_run.id}/stop"
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_transfer_owner_can_stop_run(
    client: AsyncClient,
    simple_user: MockUser,
    user_run: MockRun,
    session: AsyncSession,
) -> None:
    result = await client.post(
        f"v1/transfers/{user_run.transfer.id}/runs/{user_run.id}/stop",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }

    result = await client.post(
        f"v1/transfers/{user_run.transfer.id}/runs/{user_run.id}/stop",
        headers={"Authorization": f"Bearer {user_run.transfer.owner_user.token}"},
    )

    await session.refresh(user_run.run)
    assert user_run.status == Status.SEND_STOP_SIGNAL

    assert result.status_code == 200
    assert result.json() == {
        "id": user_run.id,
        "transfer_id": user_run.transfer_id,
        "status": user_run.status.value,
        "log_url": user_run.log_url,
        "started_at": user_run.started_at,
        "ended_at": user_run.ended_at,
        "transfer_dump": user_run.transfer_dump,
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
            "Authorization": f"Bearer {group_run.transfer.owner_group.admin.token}"
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


async def test_group_admin_cannot_stop_run_of_other_group_transfer(
    client: AsyncClient,
    user_run: MockRun,
    group_run: MockRun,
    empty_group: MockGroup,
    session: AsyncSession,
) -> None:
    for run in (user_run, group_run):
        result = await client.post(
            f"v1/transfers/{run.transfer.id}/runs/{run.id}/stop",
            headers={"Authorization": f"Bearer {empty_group.admin.token}"},
        )
        assert result.status_code == 404
        assert result.json() == {
            "ok": False,
            "status_code": 404,
            "message": "Transfer not found",
        }
        await session.refresh(run.run)
        assert run.status != Status.SEND_STOP_SIGNAL


async def test_group_member_with_read_acl_cannot_stop_run(
    client: AsyncClient,
    group_run: MockRun,
    session: AsyncSession,
) -> None:
    member_with_read_rule = group_run.transfer.owner_group.members[0]
    result = await client.post(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {member_with_read_rule.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }
    await session.refresh(group_run.run)
    assert group_run.status != Status.SEND_STOP_SIGNAL


@pytest.mark.parametrize("member_index", (1, 2))
async def test_group_member_with_write_delete_acl_can_stop_run(
    member_index: int,
    client: AsyncClient,
    group_run: MockRun,
    session: AsyncSession,
) -> None:
    member = group_run.transfer.owner_group.members[member_index]
    result = await client.post(
        f"v1/transfers/{group_run.transfer.id}/runs/{group_run.id}/stop",
        headers={"Authorization": f"Bearer {member.token}"},
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


async def test_superuser_can_stop_run_for_any_transfer(
    client: AsyncClient,
    superuser: MockUser,
    user_run: MockRun,
    group_run: MockRun,
    session: AsyncSession,
    mocker,
) -> None:
    for run in (user_run, group_run):
        result = await client.post(
            f"v1/transfers/{run.transfer.id}/runs/{run.id}/stop",
            headers={"Authorization": f"Bearer {superuser.token}"},
        )
        await session.refresh(run.run)
        assert run.status == Status.SEND_STOP_SIGNAL

        assert result.status_code == 200
        assert result.json() == {
            "id": run.id,
            "transfer_id": run.transfer_id,
            "status": run.status.value,
            "log_url": run.log_url,
            "started_at": run.started_at,
            "ended_at": run.ended_at,
            "transfer_dump": run.transfer_dump,
        }


@pytest.mark.parametrize(
    "status", (Status.SEND_STOP_SIGNAL, Status.FINISHED, Status.FAILED, Status.STOPPED)
)
async def test_cannot_stop_run_in_status_except_started_and_created(
    status: Status,
    client: AsyncClient,
    user_run: MockRun,
    session: AsyncSession,
    mocker,
) -> None:
    user_run.run.status = status
    session.add(user_run.run)
    await session.commit()

    result = await client.post(
        f"v1/transfers/{user_run.transfer.id}/runs/{user_run.id}/stop",
        headers={"Authorization": f"Bearer {user_run.transfer.owner_user.token}"},
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": f"Cannot stop run {user_run.id}. Current status is {user_run.status}",
    }
