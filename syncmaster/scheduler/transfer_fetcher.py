# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import select

from syncmaster.db.models import Transfer
from syncmaster.scheduler.utils import get_async_engine, get_async_session

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from syncmaster.scheduler.settings import SchedulerAppSettings


class TransferFetcher:
    def __init__(self, settings: SchedulerAppSettings):
        self.settings = settings
        self.last_updated_at: datetime | None = None

    async def fetch_updated_jobs(self) -> Sequence[Transfer]:
        async with (
            get_async_engine(self.settings) as engine,
            get_async_session(engine) as session,
        ):
            query = select(Transfer)
            if self.last_updated_at is not None:
                query = query.filter(Transfer.updated_at > self.last_updated_at)

            result = await session.execute(query)
            return result.scalars().all()
