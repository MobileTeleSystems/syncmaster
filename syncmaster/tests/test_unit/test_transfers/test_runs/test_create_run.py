import pytest
from httpx import AsyncClient
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockTransfer, MockUser, TestUserRoles

from app.db.models import Run, Status

pytestmark = [pytest.mark.asyncio]


async def test_user_plus_can_create_run_of_transfer_his_group(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
    role_user_plus: TestUserRoles,
) -> None:
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_user_plus)
    mocker.patch("app.tasks.config.celery.send_task")

    run = (
        await session.scalars(
            select(Run).filter_by(transfer_id=group_transfer.id, status=Status.CREATED).order_by(desc(Run.created_at))
        )
    ).one_or_none()

    assert not run

    # Act
    result = await client.post(
        f"v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": group_transfer.id},
    )

    # Assert
    run = (
        await session.scalars(
            select(Run).filter_by(transfer_id=group_transfer.id, status=Status.CREATED).order_by(desc(Run.created_at))
        )
    ).first()

    assert result.json() == {
        "id": run.id,
        "transfer_id": run.transfer_id,
        "status": run.status.value,
        "log_url": run.log_url,
        "started_at": run.started_at,
        "ended_at": run.ended_at,
        "transfer_dump": run.transfer_dump,
    }
    assert result.status_code == 200


async def test_groupless_user_cannot_create_run(
    client: AsyncClient,
    simple_user: MockUser,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
) -> None:
    # Arrange
    mocker.patch("app.tasks.config.celery.send_task")

    # Act
    result = await client.post(
        f"v1/runs",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"transfer_id": group_transfer.id},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
    assert result.status_code == 404


async def test_group_member_cannot_create_run_of_other_group_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group: MockGroup,
    session: AsyncSession,
    mocker,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    mocker.patch("app.tasks.config.celery.send_task")
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.post(
        f"v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": group_transfer.id},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Transfer not found",
    }
    assert result.status_code == 404

    assert (
        await session.scalars(
            select(Run).filter_by(transfer_id=group_transfer.id, status=Status.CREATED).order_by(desc(Run.created_at))
        )
    ).first() is None


async def test_superuser_can_create_run(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
) -> None:
    # Arrange
    mocker.patch("app.tasks.config.celery.send_task")

    # Act
    result = await client.post(
        f"v1/runs",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"transfer_id": group_transfer.id},
    )
    run = (
        await session.scalars(
            select(Run).filter_by(transfer_id=group_transfer.id, status=Status.CREATED).order_by(desc(Run.created_at))
        )
    ).first()

    # Assert
    assert result.json() == {
        "id": run.id,
        "transfer_id": run.transfer_id,
        "status": run.status.value,
        "log_url": run.log_url,
        "started_at": run.started_at,
        "ended_at": run.ended_at,
        "transfer_dump": run.transfer_dump,
    }
    assert result.status_code == 200


async def test_unauthorized_user_cannot_create_run(
    client: AsyncClient,
    group_transfer: MockTransfer,
    mocker,
) -> None:
    # Arrange
    mocker.patch("app.tasks.config.celery.send_task")

    # Act
    result = await client.post(
        f"v1/runs",
        json={"transfer_id": group_transfer.id},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
    assert result.status_code == 401


async def test_group_member_cannot_create_run_of_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
    role_guest_plus: TestUserRoles,
) -> None:
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)
    mocker.patch("app.tasks.config.celery.send_task")

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": -1},
    )

    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_cannot_create_run_of_unknown_transfer_error(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
) -> None:
    # Arrange
    mocker.patch("app.tasks.config.celery.send_task")

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"transfer_id": -1},
    )

    # Assert
    assert result.json() == {
        "message": "Transfer not found",
        "ok": False,
        "status_code": 404,
    }
