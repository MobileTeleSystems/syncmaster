import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_unit.utils import (
    create_acl,
    create_connection,
    create_credentials,
    create_group,
    create_user,
    create_user_cm,
)
from tests.utils import MockAcl, MockConnection, MockCredentials, MockGroup, MockUser

from app.api.v1.auth.utils import sign_jwt
from app.api.v1.schemas import UserRule
from app.config import Settings
from app.db.models import ObjectType, Rule, UserGroup
from app.db.repositories.utilites import decrypt_auth_data


@pytest_asyncio.fixture
async def superuser(session: AsyncSession, settings: Settings):
    async with create_user_cm(
        session, username="superuser", is_active=True, is_superuser=True
    ) as user:
        yield MockUser(user=user, auth_token=sign_jwt(user.id, settings))


@pytest_asyncio.fixture
async def simple_user(session: AsyncSession, settings: Settings):
    async with create_user_cm(session, username="simple_user", is_active=True) as user:
        yield MockUser(user=user, auth_token=sign_jwt(user.id, settings))


@pytest_asyncio.fixture
async def inactive_user(session: AsyncSession, settings: Settings):
    async with create_user_cm(session, username="inactive_user") as user:
        yield MockUser(user=user, auth_token=sign_jwt(user.id, settings))


@pytest_asyncio.fixture
async def deleted_user(session: AsyncSession, settings: Settings):
    async with create_user_cm(
        session,
        username="deleted_user",
        is_deleted=True,
    ) as user:
        yield MockUser(user=user, auth_token=sign_jwt(user.id, settings))


@pytest_asyncio.fixture
async def empty_group(session: AsyncSession, settings) -> MockGroup:
    admin = await create_user(
        session=session, username="empty_group_admin", is_active=True
    )
    group = await create_group(session=session, name="empty_group", admin_id=admin.id)
    yield MockGroup(
        group=group,
        admin=MockUser(user=admin, auth_token=sign_jwt(admin.id, settings)),
        members=[],
    )
    await session.delete(group)
    await session.delete(admin)
    await session.commit()


@pytest_asyncio.fixture
async def not_empty_group(session: AsyncSession, settings) -> MockGroup:
    admin = await create_user(
        session=session, username="notempty_group_admin", is_active=True
    )
    group = await create_group(
        session=session, name="notempty_group", admin_id=admin.id
    )
    members: list[MockUser] = []
    for username in ("not_empty_member_1", "not_empty_member_2", "not_empty_member_3"):
        u = await create_user(session, username, is_active=True)
        members.append(MockUser(user=u, auth_token=sign_jwt(u.id, settings)))
        session.add(UserGroup(group_id=group.id, user_id=u.id))
    await session.commit()
    yield MockGroup(
        group=group,
        admin=MockUser(user=admin, auth_token=sign_jwt(admin.id, settings)),
        members=members,
    )
    await session.delete(group)
    await session.delete(admin)
    for member in members:
        await session.delete(member.user)
    await session.commit()


@pytest_asyncio.fixture
async def user_connection(session: AsyncSession, settings: Settings) -> MockConnection:
    user = await create_user(
        session=session,
        username="connection_username",
        is_active=True,
    )

    connection = await create_connection(
        session=session,
        name="user_connection",
        user_id=user.id,
    )

    credentials = await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection.id,
    )

    yield MockConnection(
        connection=connection,
        owner_user=MockUser(user=user, auth_token=sign_jwt(user.id, settings)),
        owner_group=None,
        credentials=MockCredentials(
            value=decrypt_auth_data(credentials.value, settings=settings),
            connection_id=connection.id,
        ),
    )
    await session.delete(credentials)
    await session.delete(user)
    await session.delete(connection)
    await session.commit()


@pytest_asyncio.fixture
async def group_connection(session: AsyncSession, settings: Settings) -> MockConnection:
    group_admin = await create_user(
        session=session, username="group_admin_connection", is_active=True
    )
    group = await create_group(
        session=session, name="connection_group", admin_id=group_admin.id
    )
    members: list[MockUser] = []
    for username in (
        "acl_connection_group_member_1",  # with read rule
        "acl_connection_group_member_2",  # with write rule
        "acl_connection_group_member_3",  # with delete rule
    ):
        u = await create_user(session, username, is_active=True)
        members.append(MockUser(user=u, auth_token=sign_jwt(u.id, settings)))
        session.add(UserGroup(group_id=group.id, user_id=u.id))
    await session.commit()
    connection = await create_connection(
        session=session, name="group_connection", group_id=group.id
    )

    credentials = await create_credentials(
        session=session,
        settings=settings,
        connection_id=connection.id,
    )

    acl_write = await create_acl(
        session=session,
        object_id=connection.id,
        object_type=ObjectType.CONNECTION,
        user_id=members[1].id,
        rule=Rule.WRITE,
    )
    acl_delete = await create_acl(
        session=session,
        object_id=connection.id,
        object_type=ObjectType.CONNECTION,
        user_id=members[2].id,
        rule=Rule.DELETE,
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
                user=group_admin, auth_token=sign_jwt(group_admin.id, settings)
            ),
            members=members,
        ),
        owner_user=None,
        acls=[
            MockAcl(
                acl=acl_write,
                user=members[1],
                to_object=connection,
                acl_as_str=UserRule.WRITE,
            ),
            MockAcl(
                acl=acl_delete,
                user=members[2],
                to_object=connection,
                acl_as_str=UserRule.DELETE,
            ),
        ],
    )
    await session.delete(credentials)
    await session.delete(connection)
    await session.delete(group_admin)
    await session.delete(group)
    for member in members:
        await session.delete(member.user)
    await session.commit()
