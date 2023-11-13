import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_unit.utils import (
    create_connection,
    create_credentials,
    create_group,
    create_user,
    create_user_cm,
)
from tests.utils import (
    MockConnection,
    MockCredentials,
    MockGroup,
    MockUser,
    TestUserRoles,
)

from app.api.v1.auth.utils import sign_jwt
from app.config import Settings
from app.db.models import UserGroup
from app.db.repositories.utils import decrypt_auth_data


async def create_group_member(
    username: str,
    group_id: int,
    session: AsyncSession,
    settings: Settings,
) -> MockUser:
    role_name = username.split("_")[-1]

    if role_name == "maintainer":
        role = TestUserRoles.Maintainer
    elif role_name == "user":
        role = TestUserRoles.User
    elif role_name == "guest":
        role = TestUserRoles.Guest
    else:
        raise ValueError(f"Unknown role {role_name}.")

    user = await create_user(
        session,
        username,
        is_active=True,
    )

    session.add(
        UserGroup(
            group_id=group_id,
            user_id=user.id,
            role=role,
        )
    )

    return MockUser(
        user=user,
        auth_token=sign_jwt(user.id, settings),
        role=role,
    )


@pytest_asyncio.fixture
async def superuser(session: AsyncSession, settings: Settings):
    async with create_user_cm(session, username="superuser", is_active=True, is_superuser=True) as user:
        yield MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=TestUserRoles.User,
        )


@pytest_asyncio.fixture
async def simple_user(session: AsyncSession, settings: Settings):
    async with create_user_cm(session, username="simple_user", is_active=True) as user:
        yield MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=TestUserRoles.User,
        )


@pytest_asyncio.fixture
async def inactive_user(session: AsyncSession, settings: Settings):
    async with create_user_cm(session, username="inactive_user") as user:
        yield MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=TestUserRoles.User,
        )


@pytest_asyncio.fixture
async def deleted_user(session: AsyncSession, settings: Settings):
    async with create_user_cm(
        session,
        username="deleted_user",
        is_deleted=True,
    ) as user:
        yield MockUser(
            user=user,
            auth_token=sign_jwt(user.id, settings),
            role=TestUserRoles.User,
        )


@pytest_asyncio.fixture
async def empty_group(session: AsyncSession, settings) -> MockGroup:
    admin = await create_user(
        session=session,
        username="empty_group_admin",
        is_active=True,
    )
    group = await create_group(
        session=session,
        name="empty_group",
        admin_id=admin.id,
    )
    yield MockGroup(
        group=group,
        admin=MockUser(
            user=admin,
            auth_token=sign_jwt(admin.id, settings),
            role="Owner",
        ),
        members=[],
    )
    await session.delete(group)
    await session.delete(admin)
    await session.commit()


@pytest_asyncio.fixture
async def group(session: AsyncSession, settings: Settings) -> MockGroup:
    admin = await create_user(
        session=session,
        username="notempty_group_admin",
        is_active=True,
    )
    group = await create_group(session=session, name="notempty_group", admin_id=admin.id)
    members: list[MockUser] = []
    for username in (
        "not_empty_group_member_maintainer",
        "not_empty_group_member_user",
        "not_empty_group_member_guest",
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
    yield MockGroup(
        group=group,
        admin=MockUser(
            user=admin,
            auth_token=sign_jwt(admin.id, settings),
            role="Owner",
        ),
        members=members,
    )
    await session.delete(group)
    await session.delete(admin)
    for member in members:
        await session.delete(member.user)
    await session.commit()


@pytest_asyncio.fixture
async def group_connection(
    session: AsyncSession,
    settings: Settings,
) -> MockConnection:
    group_admin = await create_user(
        session=session,
        username="group_connection_admin",
        is_active=True,
    )
    group = await create_group(
        session=session,
        name="group_for_group_connection",
        admin_id=group_admin.id,
    )
    members: list[MockUser] = []
    for username in (
        "connection_group_member_maintainer",
        "connection_group_member_user",
        "connection_group_member_guest",
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
    connection = await create_connection(
        session=session,
        name="group_for_group_connection",
        group_id=group.id,
    )

    credentials = await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection.id,
    )

    yield MockConnection(
        credentials=MockCredentials(
            value=decrypt_auth_data(credentials.value, settings=settings),
            connection_id=connection.id,
        ),
        connection=connection,
        owner_group=MockGroup(
            group=group,
            admin=MockUser(
                user=group_admin,
                auth_token=sign_jwt(group_admin.id, settings),
                role="Owner",
            ),
            members=members,
        ),
    )
    await session.delete(credentials)
    await session.delete(connection)
    await session.delete(group_admin)
    await session.delete(group)
    for member in members:
        await session.delete(member.user)
    await session.commit()
