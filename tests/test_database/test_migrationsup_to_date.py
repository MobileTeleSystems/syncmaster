import pytest
from celery.backends.database.session import ResultModelBase
from sqlalchemy.ext.asyncio import AsyncEngine

from syncmaster.db.models import Base
from tests.utils import get_diff_db_metadata

pytestmark = [pytest.mark.server]


@pytest.mark.asyncio
async def test_migrations_up_to_date(async_engine: AsyncEngine):
    async with async_engine.connect() as connection:
        diff = await connection.run_sync(get_diff_db_metadata, metadata=(Base.metadata, ResultModelBase.metadata))
    assert not diff
