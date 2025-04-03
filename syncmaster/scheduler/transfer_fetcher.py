# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from sqlalchemy import select

from syncmaster.db.models import Transfer
from syncmaster.scheduler.settings import SchedulerAppSettings as Settings
from syncmaster.scheduler.utils import get_async_engine, get_async_session


class TransferFetcher:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.last_updated_at = None

    async def fetch_updated_jobs(self) -> list[Transfer]:
        async with get_async_engine(self.settings) as engine, get_async_session(engine) as session:
            query = select(Transfer)
            if self.last_updated_at is not None:
                query = query.filter(Transfer.updated_at > self.last_updated_at)

            result = await session.execute(query)
            transfers = result.scalars().all()

        return transfers
