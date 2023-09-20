import pytest
from httpx import AsyncClient
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockTransfer, MockUser

from app.db.models import Run, Status

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_create_run(
    client: AsyncClient,
    user_transfer: MockTransfer,
    mocker,
) -> None:
    mocker.patch("app.tasks.config.celery.send_task")

    result = await client.post(f"v1/transfers/{user_transfer.id}/runs")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_transfer_owner_can_create_run(
    client: AsyncClient,
    simple_user: MockUser,
    user_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
) -> None:
    mocker.patch("app.tasks.config.celery.send_task")

    result = await client.post(
        f"v1/transfers/{user_transfer.id}/runs",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }

    result = await client.post(
        f"v1/transfers/{user_transfer.id}/runs",
        headers={"Authorization": f"Bearer {user_transfer.owner_user.token}"},
    )

    run = (
        await session.scalars(
            select(Run)
            .filter_by(transfer_id=user_transfer.id, status=Status.CREATED)
            .order_by(desc(Run.created_at))
        )
    ).first()

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


async def test_group_admin_can_create_run_of_transfer_his_group(
    client: AsyncClient,
    simple_user: MockUser,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
) -> None:
    mocker.patch("app.tasks.config.celery.send_task")

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/runs",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/runs",
        headers={"Authorization": f"Bearer {group_transfer.owner_group.admin.token}"},
    )

    run = (
        await session.scalars(
            select(Run)
            .filter_by(transfer_id=group_transfer.id, status=Status.CREATED)
            .order_by(desc(Run.created_at))
        )
    ).first()

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


async def test_group_admin_cannot_create_run_of_other_group_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    user_transfer: MockTransfer,
    empty_group: MockGroup,
    session: AsyncSession,
    mocker,
) -> None:
    mocker.patch("app.tasks.config.celery.send_task")

    for transfer in (user_transfer, group_transfer):
        result = await client.post(
            f"v1/transfers/{transfer.id}/runs",
            headers={"Authorization": f"Bearer {empty_group.admin.token}"},
        )
        assert result.status_code == 404
        assert result.json() == {
            "ok": False,
            "status_code": 404,
            "message": "Transfer not found",
        }
        assert (
            await session.scalars(
                select(Run)
                .filter_by(transfer_id=transfer.id, status=Status.CREATED)
                .order_by(desc(Run.created_at))
            )
        ).first() is None


async def test_group_member_with_read_acl_cannot_create_run(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
) -> None:
    mocker.patch("app.tasks.config.celery.send_task")

    member_with_read_rule = group_transfer.owner_group.members[0]

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/runs",
        headers={"Authorization": f"Bearer {member_with_read_rule.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }
    assert (
        await session.scalars(
            select(Run)
            .filter_by(transfer_id=group_transfer.id, status=Status.CREATED)
            .order_by(desc(Run.created_at))
        )
    ).first() is None


@pytest.mark.parametrize("member_index", (1, 2))
async def test_group_member_with_write_delete_acl_can_create_run(
    member_index: int,
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
) -> None:
    mocker.patch("app.tasks.config.celery.send_task")

    member = group_transfer.owner_group.members[member_index]

    result = await client.post(
        f"v1/transfers/{group_transfer.id}/runs",
        headers={"Authorization": f"Bearer {member.token}"},
    )

    run = (
        await session.scalars(
            select(Run)
            .filter_by(transfer_id=group_transfer.id, status=Status.CREATED)
            .order_by(desc(Run.created_at))
        )
    ).first()

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


async def test_superuser_can_create_run_for_any_transfer(
    client: AsyncClient,
    superuser: MockUser,
    user_transfer: MockTransfer,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
) -> None:
    mocker.patch("app.tasks.config.celery.send_task")

    for transfer in (user_transfer, group_transfer):
        result = await client.post(
            f"v1/transfers/{transfer.id}/runs",
            headers={"Authorization": f"Bearer {superuser.token}"},
        )
        run = (
            await session.scalars(
                select(Run)
                .filter_by(transfer_id=transfer.id, status=Status.CREATED)
                .order_by(desc(Run.created_at))
            )
        ).first()

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
