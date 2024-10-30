# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from syncmaster.config import Settings
from syncmaster.db.factory import create_session_factory


def get_async_session(settings: Settings) -> AsyncSession:
    engine = create_async_engine(settings.build_db_connection_uri())
    session_factory = create_session_factory(engine=engine)
    return session_factory()
