from collections.abc import AsyncGenerator

import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.scheduler.transfer_job_manager import TransferJobManager
from syncmaster.settings import Settings


@pytest_asyncio.fixture
async def transfer_job_manager(session: AsyncSession, settings: Settings) -> AsyncGenerator[TransferJobManager, None]:
    transfer_job_manager = TransferJobManager(settings)
    transfer_job_manager.scheduler.start()

    yield transfer_job_manager

    transfer_job_manager.scheduler.shutdown()
    await session.execute(text("TRUNCATE TABLE apscheduler_jobs"))
    await session.commit()
