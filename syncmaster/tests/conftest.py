import asyncio
import os
import secrets
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
from tests.test_unit.conftest import add_user_to_group, create_group_member
from tests.test_unit.utils import (
    create_connection,
    create_credentials,
    create_group,
    create_queue,
    create_transfer,
    create_user,
)
from tests.utils import (
    MockConnection,
    MockCredentials,
    MockGroup,
    MockTransfer,
    MockUser,
    TestUserRoles,
    prepare_new_database,
    run_async_migrations,
)

from app.api.v1.auth.utils import sign_jwt
from app.config import Settings, TestSettings
from app.db.models import Base, Connection, Queue
from app.db.repositories.utils import decrypt_auth_data
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
    return Settings()


@pytest.fixture(scope="session")
def test_settings():
    return TestSettings()


@pytest.fixture(scope="session")
def alembic_config(settings: Settings) -> AlembicConfig:
    alembic_cfg = AlembicConfig(PROJECT_PATH / "alembic.ini")
    alembic_cfg.set_main_option("script_location", os.fspath(PROJECT_PATH / "app/db/migrations"))
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
async def client(
    settings: Settings,
    async_engine: AsyncEngine,
) -> AsyncGenerator:
    app = get_application(settings=settings)
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client


@pytest_asyncio.fixture
async def group_transfer(
    session: AsyncSession,
    settings: Settings,
) -> AsyncGenerator[MockTransfer, None]:
    group_admin = await create_user(
        session=session,
        username="group_transfer_admin",
        is_active=True,
    )
    group = await create_group(
        session=session,
        name="group_for_group_transfer",
        admin_id=group_admin.id,
    )

    queue = await create_queue(
        session=session,
        name=f"{secrets.token_hex(5)}_test_queue",
        group_id=group.id,
    )

    members: list[MockUser] = []
    for username in (
        "transfer_group_member_maintainer",
        "transfer_group_member_user",
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
        admin=MockUser(
            user=group_admin,
            auth_token=sign_jwt(group_admin.id, settings),
            role=TestUserRoles.Owner,
        ),
        members=members,
    )

    source_connection = await create_connection(
        session=session,
        name="group_transfer_source_connection",
        group_id=group.id,
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
    await session.delete(group_admin)
    await session.delete(queue)
    for member in members:
        await session.delete(member.user)
    await session.commit()


@pytest_asyncio.fixture
async def group_transfer_and_group_maintainer_plus(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_maintainer_plus: TestUserRoles,
    role_maintainer_or_below_without_guest: TestUserRoles,
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
    role_maintainer_plus: TestUserRoles,
    role_maintainer_or_below_without_guest: TestUserRoles,
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
async def group_transfer_and_group_user_plus(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_user_plus: TestUserRoles,
    role_maintainer_or_below_without_guest: TestUserRoles,
) -> str:
    user = group_transfer.owner_group.get_member_of_role(role_user_plus)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    return role_user_plus


@pytest_asyncio.fixture
async def group_transfer_and_group_connection_user_plus(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_user_plus: TestUserRoles,
    role_maintainer_or_below_without_guest: TestUserRoles,
    settings: Settings,
) -> tuple[str, Connection]:
    user = group_transfer.owner_group.get_member_of_role(role_user_plus)

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

    yield role_user_plus, connection
    await session.delete(connection)
    await session.commit()


@pytest_asyncio.fixture
async def group_transfer_and_group_user_or_below(
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,
    role_user_or_below: TestUserRoles,
    role_maintainer_or_below_without_guest: TestUserRoles,
) -> str:
    user = group_transfer.owner_group.get_member_of_role(role_user_or_below)

    await add_user_to_group(
        user=user.user,
        group_id=group_queue.group_id,
        session=session,
        role=role_maintainer_or_below_without_guest,
    )

    return role_user_or_below


@pytest_asyncio.fixture(
    params=[
        TestUserRoles.Guest,
        TestUserRoles.User,
        TestUserRoles.Maintainer,
        TestUserRoles.Owner,
    ]
)
async def role_guest_plus(request):
    """
    Guest: only can READ (only resources)
    User: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    Owner: READ, WRITE, DELETE (resources and users in own group)
    """
    return request.param


@pytest_asyncio.fixture(
    params=[
        TestUserRoles.Guest,
        TestUserRoles.User,
        TestUserRoles.Maintainer,
    ]
)
async def role_guest_plus_without_owner(request):
    """
    Guest: only can READ (only resources)
    User: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    Owner: READ, WRITE, DELETE (resources and users in own group)
    """
    return request.param


@pytest_asyncio.fixture(
    params=[
        TestUserRoles.User,
        TestUserRoles.Owner,
        TestUserRoles.Maintainer,
    ]
)
async def role_user_plus(request):
    """
    User: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    Owner: READ, WRITE, DELETE (resources and users in own group)
    """
    return request.param


@pytest_asyncio.fixture(
    params=[
        TestUserRoles.Maintainer,
        TestUserRoles.Owner,
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
        TestUserRoles.Guest,
        TestUserRoles.User,
    ]
)
async def role_user_or_below(request):
    """
    Guest: only can READ (only resources)
    User: READ, WRITE (only resources)
    """
    return request.param


@pytest_asyncio.fixture(
    params=[
        TestUserRoles.User,
        TestUserRoles.Maintainer,
    ]
)
async def role_maintainer_or_below_without_guest(request):
    """
    Guest: only can READ (only resources)
    User: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    """

    return request.param


@pytest_asyncio.fixture(
    params=[
        TestUserRoles.Guest,
        TestUserRoles.User,
        TestUserRoles.Maintainer,
    ]
)
async def role_maintainer_or_below(request):
    """
    Guest: only can READ (only resources)
    User: READ, WRITE (only resources)
    Maintainer: READ, WRITE, DELETE (only resources)
    """

    return request.param
