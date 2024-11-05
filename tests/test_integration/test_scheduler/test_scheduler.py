import asyncio

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Run, Status
from syncmaster.scheduler import TransferFetcher, TransferJobManager
from syncmaster.settings import Settings
from tests.mocks import MockTransfer

pytestmark = [pytest.mark.asyncio, pytest.mark.worker, pytest.mark.scheduler_integration]


async def test_scheduler(
    session: AsyncSession,
    settings: Settings,
    group_transfer: MockTransfer,
    transfer_job_manager: TransferJobManager,
    mock_send_task_to_tick,
    mock_add_job,
):
    transfer_fetcher = TransferFetcher(settings)
    transfers = await transfer_fetcher.fetch_updated_jobs()
    assert transfers
    assert group_transfer.transfer.id in [t.id for t in transfers]

    transfer_job_manager.update_jobs(transfers)

    job = transfer_job_manager.scheduler.get_job(str(group_transfer.id))
    assert job is not None

    await asyncio.sleep(1)  # make sure that created job with every-second cron worked

    run = await session.scalar(
        select(Run).filter_by(transfer_id=group_transfer.id).order_by(Run.created_at.desc()),
    )
    assert run is not None
    assert run.status in [Status.CREATED, Status.STARTED]

    for _ in range(3):
        await asyncio.sleep(2)
        await session.refresh(run)
        run = await session.scalar(select(Run, run.id))
        if run.status == Status.FINISHED:
            break

    assert run.status == Status.FINISHED
    assert run.ended_at is not None
