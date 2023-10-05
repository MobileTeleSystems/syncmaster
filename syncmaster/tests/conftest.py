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
from tests.test_unit.utils import (
    create_acl,
    create_connection,
    create_group,
    create_transfer,
    create_user,
)
from tests.utils import (
    MockAcl,
    MockConnection,
    MockGroup,
    MockTransfer,
    MockUser,
    prepare_new_database,
    run_async_migrations,
)

from app.api.v1.auth.utils import sign_jwt
from app.config import Settings
from app.db.models import Base, ObjectType, Rule, UserGroup
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
        bind=async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=True,
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


@pytest_asyncio.fixture
async def user_transfer(session: AsyncSession, settings: Settings) -> MockTransfer:
    user = await create_user(
        session=session, username="transfer_username", is_active=True
    )
    source_connection = await create_connection(
        session=session,
        name="user_transfer_source_connection",
        user_id=user.id,
    )
    target_connection = await create_connection(
        session=session,
        name="user_transfer_target_connection",
        user_id=user.id,
    )

    transfer = await create_transfer(
        session=session,
        name="user_transfer",
        user_id=user.id,
        source_connection_id=source_connection.id,
        target_connection_id=target_connection.id,
    )
    mock_user = MockUser(user=user, auth_token=sign_jwt(user.id, settings))
    yield MockTransfer(
        transfer=transfer,
        source_connection=MockConnection(
            connection=source_connection, owner_user=mock_user, owner_group=None
        ),
        target_connection=MockConnection(
            connection=target_connection, owner_user=mock_user, owner_group=None
        ),
        owner_user=mock_user,
        owner_group=None,
    )
    await session.delete(transfer)
    await session.delete(source_connection)
    await session.delete(target_connection)
    await session.delete(user)
    await session.commit()


@pytest_asyncio.fixture
async def group_transfer(session: AsyncSession, settings: Settings) -> MockTransfer:
    group_admin = await create_user(
        session=session, username="group_admin_connection", is_active=True
    )
    group = await create_group(
        session=session, name="connection_group", admin_id=group_admin.id
    )
    members: list[MockUser] = []
    for username in (
        "connection_group_member_1",  # with read rule
        "connection_group_member_2",  # with write rule
        "connection_group_member_3",  # with delete rule
    ):
        u = await create_user(session, username, is_active=True)
        members.append(MockUser(user=u, auth_token=sign_jwt(u.id, settings)))
        session.add(UserGroup(group_id=group.id, user_id=u.id))
    await session.commit()
    mock_group = MockGroup(
        group=group,
        admin=MockUser(user=group_admin, auth_token=sign_jwt(group_admin.id, settings)),
        members=members,
    )

    source_connection = await create_connection(
        session=session,
        name="group_transfer_source_connection",
        group_id=group.id,
    )
    target_connection = await create_connection(
        session=session,
        name="group_transfer_target_connection",
        group_id=group.id,
    )

    transfer = await create_transfer(
        session=session,
        name="group_transfer",
        group_id=group.id,
        source_connection_id=source_connection.id,
        target_connection_id=target_connection.id,
    )
    acl_write = await create_acl(
        session=session,
        object_id=transfer.id,
        object_type=ObjectType.TRANSFER,
        user_id=members[1].id,
        rule=Rule.WRITE,
    )
    acl_delete = await create_acl(
        session=session,
        object_id=transfer.id,
        object_type=ObjectType.TRANSFER,
        user_id=members[2].id,
        rule=Rule.DELETE,
    )
    yield MockTransfer(
        transfer=transfer,
        source_connection=MockConnection(
            connection=source_connection, owner_user=None, owner_group=mock_group
        ),
        target_connection=MockConnection(
            connection=target_connection, owner_user=None, owner_group=mock_group
        ),
        owner_user=None,
        owner_group=mock_group,
        acls=[
            MockAcl(acl=acl_write, user=members[1], to_object=transfer),
            MockAcl(acl=acl_delete, user=members[2], to_object=transfer),
        ],
    )
    await session.delete(transfer)
    await session.delete(source_connection)
    await session.delete(target_connection)
    await session.delete(group)
    await session.delete(group_admin)
    for member in members:
        await session.delete(member.user)
    await session.commit()
