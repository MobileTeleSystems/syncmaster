# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.config import Settings
from syncmaster.db import AuthData
from syncmaster.db.repositories import (
    ConnectionRepository,
    GroupRepository,
    QueueRepository,
    RunRepository,
    TransferRepository,
    UserRepository,
)
from syncmaster.db.repositories.credentials_repository import CredentialsRepository


class UnitOfWork:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
    ):
        self._session = session
        self.user = UserRepository(session=session)
        self.group = GroupRepository(session=session)
        self.connection = ConnectionRepository(session=session)
        self.transfer = TransferRepository(session=session)
        self.run = RunRepository(session=session)
        self.credentials = CredentialsRepository(
            session=session,
            settings=settings,
            model=AuthData,
        )
        self.queue = QueueRepository(session=session)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if exc_type:
            await self._session.rollback()
        else:
            await self._session.commit()
