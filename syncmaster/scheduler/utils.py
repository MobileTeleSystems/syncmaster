# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.factory import create_engine, create_session_factory
from syncmaster.settings import Settings


def get_async_session(settings: Settings) -> AsyncSession:
    engine = create_engine(settings.database.sync_url)
    session_factory = create_session_factory(engine=engine)
    return session_factory()
