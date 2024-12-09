from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Run, RunType, Status
from tests.mocks import MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_developer_plus_can_create_run_of_transfer_his_group(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
    role_developer_plus: UserTestRoles,
) -> None:
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)
    mock_send_task = mocker.patch("syncmaster.backend.celery.app.send_task")
    mock_to_thread = mocker.patch("asyncio.to_thread", new_callable=AsyncMock)

    run = (
        await session.scalars(
            select(Run).filter_by(transfer_id=group_transfer.id, status=Status.CREATED).order_by(desc(Run.created_at)),
        )
    ).one_or_none()

    assert not run

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": group_transfer.id},
    )

    # Assert
    run = (
        await session.scalars(
            select(Run).filter_by(transfer_id=group_transfer.id, status=Status.CREATED).order_by(desc(Run.created_at)),
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
        "type": RunType.MANUAL,
    }
    assert result.status_code == 200

    mock_to_thread.assert_awaited_once_with(
        mock_send_task,
        "run_transfer_task",
        kwargs={"run_id": run.id},
        queue=group_transfer.queue.name,
    )


async def test_groupless_user_cannot_create_run(
    client: AsyncClient,
    simple_user: MockUser,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
) -> None:
    # Arrange
    mocker.patch("syncmaster.backend.celery.app.send_task")
    mocker.patch("asyncio.to_thread", new_callable=AsyncMock)

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"transfer_id": group_transfer.id},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_group_member_cannot_create_run_of_other_group_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group: MockGroup,
    session: AsyncSession,
    mocker,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    mocker.patch("syncmaster.backend.celery.app.send_task")
    mocker.patch("asyncio.to_thread", new_callable=AsyncMock)
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": group_transfer.id},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }
    assert result.status_code == 404

    assert (
        await session.scalars(
            select(Run).filter_by(transfer_id=group_transfer.id, status=Status.CREATED).order_by(desc(Run.created_at)),
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
    mock_send_task = mocker.patch("syncmaster.backend.celery.app.send_task")
    mock_to_thread = mocker.patch("asyncio.to_thread", new_callable=AsyncMock)

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"transfer_id": group_transfer.id},
    )
    run = (
        await session.scalars(
            select(Run).filter_by(transfer_id=group_transfer.id, status=Status.CREATED).order_by(desc(Run.created_at)),
        )
    ).first()

    # Assert
    response = result.json()
    assert response == {
        "id": run.id,
        "transfer_id": run.transfer_id,
        "status": run.status.value,
        "log_url": run.log_url,
        "started_at": run.started_at,
        "ended_at": run.ended_at,
        "transfer_dump": run.transfer_dump,
        "type": RunType.MANUAL,
    }
    assert result.status_code == 200
    assert "correlation_id" in response.get("log_url")
    assert "run_id" in response.get("log_url")
    mock_to_thread.assert_awaited_once_with(
        mock_send_task,
        "run_transfer_task",
        kwargs={"run_id": run.id},
        queue=group_transfer.queue.name,
    )


async def test_unauthorized_user_cannot_create_run(
    client: AsyncClient,
    group_transfer: MockTransfer,
    mocker,
) -> None:
    # Arrange
    mocker.patch("syncmaster.backend.celery.app.send_task")
    mocker.patch("asyncio.to_thread", new_callable=AsyncMock)

    # Act
    result = await client.post(
        "v1/runs",
        json={"transfer_id": group_transfer.id},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }
    assert result.status_code == 401


async def test_group_member_cannot_create_run_of_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
    role_guest_plus: UserTestRoles,
) -> None:
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)
    mocker.patch("syncmaster.backend.celery.app.send_task")
    mocker.patch("asyncio.to_thread", new_callable=AsyncMock)

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": -1},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_superuser_cannot_create_run_of_unknown_transfer_error(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
    session: AsyncSession,
    mocker,
) -> None:
    # Arrange
    mocker.patch("syncmaster.backend.celery.app.send_task")
    mocker.patch("asyncio.to_thread", new_callable=AsyncMock)

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={"transfer_id": -1},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }
