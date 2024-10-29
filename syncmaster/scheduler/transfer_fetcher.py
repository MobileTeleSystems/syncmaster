# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from syncmaster.config import Settings
from syncmaster.db.models import Transfer

DATABASE_URL = Settings().build_db_connection_uri()
engine = create_async_engine(DATABASE_URL, echo=True)
AsyncSessionLocal = sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)


class TransferFetcher:
    def __init__(self):
        self.last_updated_at = None

    async def fetch_updated_jobs(self):

        async with AsyncSessionLocal() as session:
            if self.last_updated_at is None:
                query = select(Transfer).filter(Transfer.is_scheduled == True)
            else:
                query = select(Transfer).filter(Transfer.updated_at > self.last_updated_at)
            result = await session.execute(query)
            transfers = result.scalars().all()

        return transfers
