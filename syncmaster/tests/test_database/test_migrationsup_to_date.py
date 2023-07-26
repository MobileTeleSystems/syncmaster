import pytest
from sqlalchemy.ext.asyncio import AsyncEngine

from app.db.models import Base
from tests.utils import get_diff_db_metadata


@pytest.mark.asyncio
async def test_migrations_up_to_date(async_engine: AsyncEngine):
    async with async_engine.connect() as connection:
        diff = await connection.run_sync(get_diff_db_metadata, metadata=Base.metadata)
    assert not diff
