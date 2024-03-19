import asyncio
import logging
import os
import secrets
from collections.abc import AsyncGenerator
from datetime import datetime
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

from syncmaster.backend.api.v1.auth.utils import sign_jwt
from syncmaster.backend.main import get_application
from syncmaster.config import Settings, TestSettings
from syncmaster.db.models import Base, Connection, Queue
from syncmaster.db.repositories.utils import decrypt_auth_data
from tests.mocks import (
    MockConnection,
    MockCredentials,
    MockGroup,
    MockTransfer,
    MockUser,
    UserTestRoles,
    prepare_new_database,
    run_async_migrations,
)
from tests.test_unit.conftest import add_user_to_group, create_group_member
from tests.test_unit.utils import (
    create_connection,
    create_credentials,
    create_group,
    create_queue,
    create_transfer,
    create_user,
)

PROJECT_PATH = Path(__file__).parent.parent.resolve()


logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def settings():
    return Settings()


@pytest.fixture(scope="session")
def test_settings():
    return TestSettings()


@pytest.fixture(scope="session")
def alembic_config(settings: Settings) -> AlembicConfig:
    alembic_cfg = AlembicConfig(PROJECT_PATH / "syncmaster" / "db" / "alembic.ini")
    alembic_cfg.set_main_option("script_location", os.fspath(PROJECT_PATH / "syncmaster/db/migrations"))
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
    )


@pytest_asyncio.fixture
async def session(sessionmaker: async_sessionmaker[AsyncSession]):
    try:
        session: AsyncSession = sessionmaker()
        yield session
    finally:
        await session.close()


@pytest_asyncio.fixture(scope="session")
async def client(
    settings: Settings,
    async_engine: AsyncEngine,
) -> AsyncGenerator:
    logger.info("START CLIENT FIXTURE", datetime.now().isoformat())
    app = get_application(settings=settings)
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client
        logger.info("END CLIENT FIXTURE", datetime.now().isoformat())


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


@pytest_asyncio.fixture
async def group_transfer(
    session: AsyncSession,
    settings: Settings,
    create_connection_data: dict | None,
    create_transfer_data: dict | None,
) -> AsyncGenerator[MockTransfer, None]:
    group_owner = await create_user(
        session=session,
        username="group_transfer_owner",
        is_active=True,
    )
    group = await create_group(
        session=session,
        name="group_for_group_transfer",
        owner_id=group_owner.id,
    )

    queue = await create_queue(
        session=session,
        name=f"{secrets.token_hex(5)}_test_queue",
        group_id=group.id,
    )

    members: list[MockUser] = []
    for username in (
        "transfer_group_member_maintainer",
        "transfer_group_member_developer",
        "transfer_group_member_guest",
    ):
        members.append(
            await create_group_member(
                username=username,
                group_id=group.id,
                session=session,
                settings=settings,
            )
        )

    await session.commit()
    mock_group = MockGroup(
        group=group,
        owner=MockUser(
            user=group_owner,
            auth_token=sign_jwt(group_owner.id, settings),
            role=UserTestRoles.Owner,
        ),
        members=members,
    )

    source_connection = await create_connection(
        session=session,
        name="group_transfer_source_connection",
        group_id=group.id,
        data=create_connection_data,
    )
    source_connection_creds = await create_credentials(
        session=session,
        settings=settings,
        connection_id=source_connection.id,
    )
    target_connection = await create_connection(
        session=session,
        name="group_transfer_target_connection",
        group_id=group.id,
        data=create_connection_data,
    )
    target_connection_creds = await create_credentials(
        session=session,
        settings=settings,
        connection_id=target_connection.id,
    )

    transfer = await create_transfer(
        session=session,
        name="group_transfer",
        group_id=group.id,
        source_connection_id=source_connection.id,
        target_connection_id=target_connection.id,
        queue_id=queue.id,
        source_params=create_transfer_data,
        target_params=create_transfer_data,
    )

    yield MockTransfer(
        transfer=transfer,
        source_connection=MockConnection(
            connection=source_connection,
            owner_group=mock_group,
            credentials=MockCredentials(
                value=decrypt_auth_data(source_connection_creds.value, settings=settings),
                connection_id=source_connection.id,
            ),
        ),
        target_connection=MockConnection(
            connection=target_connection,
            owner_group=mock_group,
            credentials=MockCredentials(
                value=decrypt_auth_data(target_connection_creds.value, settings=settings),
                connection_id=target_connection.id,
            ),
        ),
        owner_group=mock_group,
    )
    await session.delete(transfer)
    await session.delete(source_connection)
    await session.delete(target_connection)
    await session.delete(group)
    await session.delete(group_owner)
    await session.delete(queue)
    for member in members:
        await session.delete(member.user)
    await session.commit()


@pytest_asyncio.fixture
async def group_transfer_and_group_maintainer_plus(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_maintainer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> str:
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    return role_maintainer_plus


@pytest_asyncio.fixture
async def group_transfer_with_same_name_maintainer_plus(
    session: AsyncSession,
    settings: Settings,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_maintainer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> str:
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    source_connection = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        group_id=group_queue.group_id,
    )
    await create_credentials(
        session=session,
        settings=settings,
        connection_id=source_connection.id,
    )
    target_connection = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        group_id=group_queue.group_id,
    )
    await create_credentials(
        session=session,
        settings=settings,
        connection_id=target_connection.id,
    )

    transfer = await create_transfer(
        session=session,
        name="duplicated_group_transfer",
        group_id=group_queue.group_id,
        source_connection_id=source_connection.id,
        target_connection_id=target_connection.id,
        queue_id=group_queue.id,
    )

    yield role_maintainer_plus
    await session.delete(source_connection)
    await session.delete(target_connection)
    await session.delete(transfer)
    await session.commit()


@pytest_asyncio.fixture
async def group_transfer_with_same_name(
    session: AsyncSession,
    settings: Settings,
    group_queue: Queue,
    group_transfer: MockTransfer,
) -> None:
    source_connection = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        group_id=group_queue.group_id,
    )
    await create_credentials(
        session=session,
        settings=settings,
        connection_id=source_connection.id,
    )
    target_connection = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        group_id=group_queue.group_id,
    )
    await create_credentials(
        session=session,
        settings=settings,
        connection_id=target_connection.id,
    )

    transfer = await create_transfer(
        session=session,
        name="duplicated_group_transfer",
        group_id=group_queue.group_id,
        source_connection_id=source_connection.id,
        target_connection_id=target_connection.id,
        queue_id=group_queue.id,
    )

    yield
    await session.delete(source_connection)
    await session.delete(target_connection)
    await session.delete(transfer)
    await session.commit()


@pytest_asyncio.fixture
async def group_transfer_and_group_developer_plus(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> str:
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    return role_developer_plus


@pytest_asyncio.fixture
async def group_transfer_and_group_connection_developer_plus(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_developer_plus: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
    settings: Settings,
) -> tuple[str, Connection]:
    user = group_transfer.owner_group.get_member_of_role(role_developer_plus)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    connection = await create_connection(
        session=session,
        name="group_transfer_source_connection",
        group_id=group_queue.group_id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection.id,
    )

    yield role_developer_plus, connection
    await session.delete(connection)
    await session.commit()


@pytest_asyncio.fixture
async def group_transfer_and_group_developer_or_below(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_developer_or_below: UserTestRoles,
    role_maintainer_or_below_without_guest: UserTestRoles,
) -> str:
    user = group_transfer.owner_group.get_member_of_role(role_developer_or_below)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    return role_developer_or_below


@pytest_asyncio.fixture(
    params=[
        UserTestRoles.Guest,
        UserTestRoles.Developer,
        UserTestRoles.Maintainer,
        UserTestRoles.Owner,
    ]
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
    ]
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
    ]
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
    ]
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
    ]
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
    ]
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
    ]
)
async def role_maintainer_or_below(request):
    """
    Guest: only can READ (only resources)
    Developer: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    """

    return request.param
