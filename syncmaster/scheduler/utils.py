# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from syncmaster.settings import Settings

TRANSFER_FETCHING_TIMEOUT = 180  # seconds
MISFIRE_GRACE_TIME = 300  # seconds


def get_async_session(settings: Settings) -> AsyncSession:
    engine = create_async_engine(settings.database.url)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    return session_factory()
