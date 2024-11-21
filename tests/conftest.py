import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator, Callable
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

from syncmaster.backend import application_factory
from syncmaster.backend.settings import ServerAppSettings as Settings
from syncmaster.backend.settings.auth.jwt import JWTSettings
from syncmaster.backend.utils.jwt import sign_jwt
from syncmaster.db.models import Base
from syncmaster.scheduler.settings import SchedulerAppSettings
from tests.mocks import UserTestRoles
from tests.settings import TestSettings
from tests.utils import prepare_new_database, run_async_migrations

PROJECT_PATH = Path(__file__).parent.parent.resolve()


logger = logging.getLogger(__name__)

pytest_plugins = [
    "tests.test_unit.test_transfers.transfer_fixtures",
    "tests.test_unit.test_auth.auth_fixtures",
    "tests.test_unit.test_users.user_fixtures",
    "tests.test_unit.test_runs.run_fixtures",
    "tests.test_unit.test_connections.connection_fixtures",
    "tests.test_unit.test_scheduler.scheduler_fixtures",
    "tests.test_integration.test_scheduler.scheduler_fixtures",
]


@pytest.fixture
def access_token_settings(settings: Settings) -> JWTSettings:
    return JWTSettings.parse_obj(settings.auth.access_token)


@pytest.fixture
def access_token_factory(access_token_settings: JWTSettings) -> Callable[[int], str]:
    def _generate_access_token(user_id: int) -> str:
        return sign_jwt(
            {"user_id": user_id, "exp": time.time() + 1000},
            access_token_settings.secret_key.get_secret_value(),
            access_token_settings.security_algorithm,
        )

    return _generate_access_token


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", params=[{}])
def settings(request: pytest.FixtureRequest) -> Settings:
    return Settings.parse_obj(request.param)


@pytest.fixture(scope="session", params=[{}])
def scheduler_settings(request: pytest.FixtureRequest) -> SchedulerAppSettings:
    return SchedulerAppSettings.parse_obj(request.param)


@pytest.fixture(scope="session")
def test_settings():
    return TestSettings()


@pytest.fixture(scope="session")
def alembic_config(settings: Settings) -> AlembicConfig:
    alembic_cfg = AlembicConfig(PROJECT_PATH / "syncmaster" / "db" / "alembic.ini")
    alembic_cfg.set_main_option("script_location", os.fspath(PROJECT_PATH / "syncmaster/db/migrations"))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database.url)
    return alembic_cfg


@pytest_asyncio.fixture(scope="session")
async def async_engine(settings: Settings, alembic_config: AlembicConfig):
    await prepare_new_database(settings=settings)
    try:
        await run_async_migrations(alembic_config, Base.metadata, "-1", "down")
    except Exception:
        pass
    await run_async_migrations(alembic_config, Base.metadata, "head")
    engine = create_async_engine(settings.database.url)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def sessionmaker(async_engine: AsyncEngine):
    yield async_sessionmaker(
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


@pytest_asyncio.fixture
async def session(sessionmaker: async_sessionmaker[AsyncSession]):
    try:
        session: AsyncSession = sessionmaker()
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture(scope="session")
async def client(settings: Settings) -> AsyncGenerator:
    logger.info("START CLIENT FIXTURE")
    app = application_factory(settings=settings)
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
        logger.info("END CLIENT FIXTURE")


@pytest_asyncio.fixture
async def create_connection_data(request):
    if hasattr(request, "param"):
        return request.param
    return None


@pytest_asyncio.fixture
async def create_transfer_data(request):
    if hasattr(request, "param"):
        return request.param
    return None


@pytest_asyncio.fixture(
    params=[
        UserTestRoles.Guest,
        UserTestRoles.Developer,
        UserTestRoles.Maintainer,
        UserTestRoles.Owner,
    ],
)
async def role_guest_plus(request):
    """
    Guest: only can READ (only resources)
    Developer: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    Owner: READ, WRITE, DELETE (resources and users in own group)
    """
    return request.param


@pytest_asyncio.fixture(
    params=[
        UserTestRoles.Guest,
        UserTestRoles.Developer,
        UserTestRoles.Maintainer,
    ],
)
async def role_guest_plus_without_owner(request):
    """
    Guest: only can READ (only resources)
    Developer: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    Owner: READ, WRITE, DELETE (resources and users in own group)
    """
    return request.param


@pytest_asyncio.fixture(
    params=[
        UserTestRoles.Developer,
        UserTestRoles.Owner,
        UserTestRoles.Maintainer,
    ],
)
async def role_developer_plus(request):
    """
    Developer: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    Owner: READ, WRITE, DELETE (resources and users in own group)
    """
    return request.param


@pytest_asyncio.fixture(
    params=[
        UserTestRoles.Maintainer,
        UserTestRoles.Owner,
    ],
)
async def role_maintainer_plus(request):
    """
    Maintainer: READ, WRITE, DELETE (only resources)
    Owner: READ, WRITE, DELETE (resources and users in own group)
    """
    return request.param


@pytest_asyncio.fixture(
    params=[
        UserTestRoles.Guest,
        UserTestRoles.Developer,
    ],
)
async def role_developer_or_below(request):
    """
    Guest: only can READ (only resources)
    Developer: READ, WRITE (only resources)
    """
    return request.param


@pytest_asyncio.fixture(
    params=[
        UserTestRoles.Developer,
        UserTestRoles.Maintainer,
    ],
)
async def role_maintainer_or_below_without_guest(request):
    """
    Guest: only can READ (only resources)
    Developer: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    """

    return request.param


@pytest_asyncio.fixture(
    params=[
        UserTestRoles.Guest,
        UserTestRoles.Developer,
        UserTestRoles.Maintainer,
    ],
)
async def role_maintainer_or_below(request):
    """
    Guest: only can READ (only resources)
    Developer: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    """

    return request.param
