import asyncio
import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
import pytest_asyncio
from alembic.config import Config as AlembicConfig
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import Settings
from app.db.models import Base
from app.main import get_application
from tests.utils import prepare_new_database, run_async_migrations

PROJECT_PATH = Path(__file__).parent.parent.resolve()


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def fxtr_settings():
    settings = Settings()
    settings.POSTGRES_DB = "test_" + settings.POSTGRES_DB
    return settings


@pytest.fixture(scope="session")
def alembic_config(fxtr_settings: Settings) -> AlembicConfig:
    alembic_cfg = AlembicConfig(PROJECT_PATH / "alembic.ini")
    alembic_cfg.set_main_option(
        "script_location", os.fspath(PROJECT_PATH / "app/db/migrations")
    )
    alembic_cfg.set_main_option(
        "sqlalchemy.url", fxtr_settings.build_db_connection_uri()
    )
    return alembic_cfg


@pytest_asyncio.fixture(scope="session")
async def async_engine(fxtr_settings: Settings, alembic_config: AlembicConfig):
    await prepare_new_database(settings=fxtr_settings)
    await run_async_migrations(alembic_config, Base.metadata, "head")
    engine = create_async_engine(fxtr_settings.build_db_connection_uri(), echo=True)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def sessionmaker(async_engine: AsyncEngine):
    yield async_sessionmaker(
        bind=async_engine, class_=AsyncSession, expire_on_commit=False, autoflush=True
    )


@pytest_asyncio.fixture
async def session(sessionmaker: async_sessionmaker[AsyncSession]):
    try:
        session: AsyncSession = sessionmaker()
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture(scope="session")
async def client(fxtr_settings, async_engine) -> AsyncGenerator:
    app = get_application(settings=fxtr_settings)

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
