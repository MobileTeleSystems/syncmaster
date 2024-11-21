# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.dependencies import Stub
from syncmaster.backend.settings import ServerAppSettings as Settings
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


class UnitOfWork:
    def __init__(
        self,
        settings: Annotated[Settings, Depends(Stub(Settings))],
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
