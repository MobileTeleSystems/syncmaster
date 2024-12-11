from unittest.mock import AsyncMock

import pytest
from apscheduler.triggers.cron import CronTrigger
from kombu.exceptions import KombuError
from pytest_mock import MockerFixture
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Run, Status
from syncmaster.exceptions.run import CannotConnectToTaskQueueError
from syncmaster.scheduler.transfer_job_manager import TransferJobManager
from tests.mocks import MockTransfer

pytestmark = [pytest.mark.asyncio, pytest.mark.scheduler]


async def test_adding_new_jobs(transfer_job_manager: TransferJobManager, group_transfers: list[MockTransfer]):
    # Act
    transfer_job_manager.update_jobs(group_transfers)

    # Assert
    for transfer in group_transfers:
        job = transfer_job_manager.scheduler.get_job(str(transfer.transfer.id))
        assert job is not None
        assert job.trigger.fields == CronTrigger.from_crontab(transfer.transfer.schedule).fields


async def test_modifying_existing_jobs(transfer_job_manager: TransferJobManager, group_transfers: list[MockTransfer]):
    # Arrange
    transfer_job_manager.update_jobs(group_transfers)
    modified_transfer = group_transfers[0]
    expected_cron = "0 2 * * *"
    modified_transfer.transfer.schedule = expected_cron

    # Act
    transfer_job_manager.update_jobs([modified_transfer])
    job = transfer_job_manager.scheduler.get_job(str(modified_transfer.transfer.id))

    # Assert
    assert job is not None
    assert job.trigger.fields == CronTrigger.from_crontab(expected_cron).fields


@pytest.mark.parametrize(
    "transfer_attr, expected_state, is_existing_job",
    [
        ("is_deleted", True, True),
        ("is_deleted", True, False),
        ("is_scheduled", False, True),
        ("is_scheduled", False, False),
    ],
)
async def test_handling_irrelevant_jobs(
    transfer_job_manager: TransferJobManager,
    group_transfers: list[MockTransfer],
    transfer_attr: str,
    expected_state: bool,
    is_existing_job: bool,
):
    # Arrange
    if is_existing_job:
        transfer_job_manager.update_jobs(group_transfers)

    test_transfer = group_transfers[0]
    setattr(test_transfer.transfer, transfer_attr, expected_state)

    # Act
    transfer_job_manager.update_jobs([test_transfer])
    job = transfer_job_manager.scheduler.get_job(str(test_transfer.transfer.id))

    # Assert
    assert job is None


async def test_send_job_to_celery_with_success(
    mocker: MockerFixture,
    session: AsyncSession,
    transfer_job_manager: TransferJobManager,
    group_transfer: MockTransfer,
):
    # Arrange
    mock_send_task = mocker.patch("syncmaster.scheduler.celery.app.send_task")
    mock_to_thread = mocker.patch("asyncio.to_thread", new_callable=AsyncMock)

    # Act
    await transfer_job_manager.send_job_to_celery(group_transfer.transfer.id)
    run = (
        await session.scalars(
            select(Run).filter_by(transfer_id=group_transfer.id, status=Status.CREATED).order_by(desc(Run.created_at)),
        )
    ).first()

    # Assert
    mock_to_thread.assert_awaited_once_with(
        mock_send_task,
        "run_transfer_task",
        kwargs={"run_id": run.id},
        queue=group_transfer.queue.slug,
    )


async def test_send_job_to_celery_with_failure(
    mocker: MockerFixture,
    session: AsyncSession,
    transfer_job_manager: TransferJobManager,
    group_transfer: MockTransfer,
):
    # Arrange
    mocker.patch("syncmaster.scheduler.celery.app.send_task")
    mocker.patch("asyncio.to_thread", new_callable=AsyncMock, side_effect=KombuError)

    # Act & Assert
    with pytest.raises(CannotConnectToTaskQueueError) as exc_info:
        await transfer_job_manager.send_job_to_celery(group_transfer.transfer.id)

    assert exc_info.value.run_id is not None

    run = (
        await session.scalars(
            select(Run).filter_by(transfer_id=group_transfer.id).order_by(desc(Run.created_at)),
        )
    ).first()

    assert run is not None
    assert run.status == Status.FAILED
