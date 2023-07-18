import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.api.v1.auth.utils import sign_jwt
from app.config import Settings, get_settings
from app.db.models import Base, User
from app.main import get_application
from tests.utils import MockUser, create_database, database_exists, drop_database


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def fxtr_settings():
    settings = get_settings()
    settings.POSTGRES_DB = "test_" + settings.POSTGRES_DB
    return settings


@pytest_asyncio.fixture(scope="session")
async def init_database(fxtr_settings: Settings):
    test_db_name = fxtr_settings.POSTGRES_DB

    fxtr_settings.POSTGRES_DB = "postgres"
    engine = create_async_engine(fxtr_settings.DATABASE_URI, echo=True)
    async with engine.begin() as conn:
        if await database_exists(conn, test_db_name):
            await drop_database(conn, test_db_name)
        await create_database(conn, test_db_name)
    await engine.dispose()
    fxtr_settings.POSTGRES_DB = test_db_name
    engine = create_async_engine(fxtr_settings.DATABASE_URI, echo=True)
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
async def async_client(init_database) -> AsyncGenerator:
    app = get_application()

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def superuser(session: AsyncSession, fxtr_settings: Settings):
    sa_u = User(username="superuser", is_superuser=True, is_active=True)
    session.add(sa_u)
    await session.commit()
    await session.refresh(sa_u)
    yield MockUser(user=sa_u, auth_token=sign_jwt(sa_u.id, fxtr_settings))
    await session.delete(sa_u)
    await session.commit()


@pytest_asyncio.fixture
async def simple_user(session: AsyncSession, fxtr_settings: Settings):
    sa_u = User(username="simple_user", is_superuser=False, is_active=True)
    session.add(sa_u)
    await session.commit()
    await session.refresh(sa_u)
    yield MockUser(user=sa_u, auth_token=sign_jwt(sa_u.id, fxtr_settings))
    await session.delete(sa_u)
    await session.commit()


@pytest_asyncio.fixture
async def inactive_user(session: AsyncSession, fxtr_settings: Settings):
    sa_u = User(username="inactive_user", is_superuser=False, is_active=False)
    session.add(sa_u)
    await session.commit()
    await session.refresh(sa_u)
    yield MockUser(user=sa_u, auth_token=sign_jwt(sa_u.id, fxtr_settings))
    await session.delete(sa_u)
    await session.commit()


@pytest_asyncio.fixture
async def deleted_user(session: AsyncSession, fxtr_settings: Settings):
    sa_u = User(
        username="deleted_user", is_superuser=False, is_active=False, is_deleted=True
    )
    session.add(sa_u)
    await session.commit()
    await session.refresh(sa_u)
    yield MockUser(user=sa_u, auth_token=sign_jwt(sa_u.id, fxtr_settings))
    await session.delete(sa_u)
    await session.commit()
