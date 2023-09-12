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
from tests.utils import prepare_new_database, run_async_migrations

from app.config import Settings
from app.db.models import Base
from app.main import get_application

PROJECT_PATH = Path(__file__).parent.parent.resolve()


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings():
    settings = Settings()
    settings.POSTGRES_DB = settings.POSTGRES_DB
    return settings


@pytest.fixture(scope="session")
def alembic_config(settings: Settings) -> AlembicConfig:
    alembic_cfg = AlembicConfig(PROJECT_PATH / "alembic.ini")
    alembic_cfg.set_main_option(
        "script_location", os.fspath(PROJECT_PATH / "app/db/migrations")
    )
    alembic_cfg.set_main_option("sqlalchemy.url", settings.build_db_connection_uri())
    return alembic_cfg


@pytest_asyncio.fixture(scope="session")
async def async_engine(settings: Settings, alembic_config: AlembicConfig):
    await prepare_new_database(settings=settings)
    try:
        await run_async_migrations(alembic_config, Base.metadata, "-1", "down")
    except Exception:
        pass
    await run_async_migrations(alembic_config, Base.metadata, "head")
    engine = create_async_engine(settings.build_db_connection_uri())
    yield engine
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
async def client(settings: Settings, async_engine: AsyncEngine) -> AsyncGenerator:
    app = get_application(settings=settings)
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
