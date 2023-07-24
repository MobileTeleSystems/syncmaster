import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import Settings
from app.db.models import Base
from app.main import get_application
from tests.utils import prepare_new_database


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def fxtr_settings():
    settings = Settings()
    settings.POSTGRES_DB = "test_" + settings.POSTGRES_DB
    return settings


@pytest_asyncio.fixture(scope="session")
async def init_database(fxtr_settings: Settings):
    await prepare_new_database(settings=fxtr_settings)
    engine = create_async_engine(fxtr_settings.build_db_connection_uri(), echo=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False, autoflush=True
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture
async def session(init_database):
    try:
        session: AsyncSession = init_database()
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture(scope="session")
async def client(fxtr_settings, init_database) -> AsyncGenerator:
    app = get_application(settings=fxtr_settings)

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
