# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from collections.abc import AsyncGenerator, Callable
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from syncmaster.server.services.unit_of_work import UnitOfWork
from syncmaster.server.settings import ServerAppSettings as Settings


def create_engine(connection_uri: str, **engine_kwargs: Any) -> AsyncEngine:
    return create_async_engine(url=connection_uri, **engine_kwargs)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


def get_uow(
    session_factory: async_sessionmaker[AsyncSession],
    settings: Settings,
) -> Callable[[], AsyncGenerator[UnitOfWork, None]]:
    async def wrapper():
        async with session_factory() as session:
            yield UnitOfWork(session=session, settings=settings)

    return wrapper
