# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import AuthData
from syncmaster.db.repositories import (
    ConnectionRepository,
    CredentialsRepository,
    GroupRepository,
    QueueRepository,
    RunRepository,
    TransferRepository,
    UserRepository,
)
from syncmaster.scheduler.settings import SchedulerAppSettings
from syncmaster.server.dependencies import Stub
from syncmaster.server.settings import ServerAppSettings
from syncmaster.worker.settings import WorkerAppSettings


class UnitOfWork:
    def __init__(
        self,
        settings: Annotated[
            SchedulerAppSettings | ServerAppSettings | WorkerAppSettings, Depends(Stub(ServerAppSettings))
        ],
        session: Annotated[AsyncSession, Depends(Stub(AsyncSession))],
    ):
        self._session = session
        self.user = UserRepository(session=session)
        self.group = GroupRepository(session=session)
        self.connection = ConnectionRepository(session=session)
        self.transfer = TransferRepository(session=session)
        self.run = RunRepository(session=session)
        self.credentials = CredentialsRepository(
            session=session,
            model=AuthData,
            settings=settings,
        )
        self.queue = QueueRepository(session=session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            await self._session.rollback()
        else:
            await self._session.commit()
