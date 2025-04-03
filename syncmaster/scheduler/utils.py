# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import contextlib
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from syncmaster.scheduler.settings import SchedulerAppSettings as Settings


@contextlib.asynccontextmanager
async def get_async_engine(settings: Settings) -> AsyncGenerator[AsyncEngine, None]:
    engine = create_async_engine(url=settings.database.url)
    try:
        yield engine
    finally:
        await engine.dispose()


def get_async_session(engine: AsyncEngine) -> AsyncSession:
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return session_factory()
