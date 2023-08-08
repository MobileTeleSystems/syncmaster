import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.utils import sign_jwt
from app.config import Settings
from app.db.models import ObjectType, Rule, UserGroup
from tests.test_unit.utils import (
    create_acl,
    create_connection,
    create_group,
    create_user,
)
from tests.utils import MockAcl, MockConnection, MockGroup, MockUser


@pytest_asyncio.fixture
async def user_connection(
    session: AsyncSession, fxtr_settings: Settings
) -> MockConnection:
    user = await create_user(
        session=session, username="connection_username", is_active=True
    )
    connection = await create_connection(
        session=session, name="user_connection", user_id=user.id, group_id=None
    )
    yield MockConnection(
        connection=connection,
        owner_user=MockUser(user=user, auth_token=sign_jwt(user.id, fxtr_settings)),
        owner_group=None,
    )
    await session.delete(connection)
    await session.delete(user)
    await session.commit()


@pytest_asyncio.fixture
async def group_connection(
    session: AsyncSession, fxtr_settings: Settings
) -> MockConnection:
    group_admin = await create_user(
        session=session, username="group_admin_connection", is_active=True
    )
    group = await create_group(
        session=session, name="connection_group", admin_id=group_admin.id
    )
    members: list[MockUser] = []
    for username in (
        "connection_group_member_1",
        "connection_group_member_2",
        "connection_group_member_3",
    ):
        u = await create_user(session, username, is_active=True)
        members.append(MockUser(user=u, auth_token=sign_jwt(u.id, fxtr_settings)))
        session.add(UserGroup(group_id=group.id, user_id=u.id))
    await session.commit()
    connection = await create_connection(
        session=session, name="group_connection", user_id=None, group_id=group.id
    )
    yield MockConnection(
        connection=connection,
        owner_group=MockGroup(
            group=group,
            admin=MockUser(
                user=group_admin, auth_token=sign_jwt(group_admin.id, fxtr_settings)
            ),
            members=members,
        ),
        owner_user=None,
    )
    await session.delete(connection)
    await session.delete(group)
    await session.delete(group_admin)
    for member in members:
        await session.delete(member.user)
    await session.commit()


@pytest_asyncio.fixture
async def group_connection_with_acl(
    session: AsyncSession, fxtr_settings: Settings
) -> MockConnection:
    group_admin = await create_user(
        session=session, username="acl_group_admin_connection", is_active=True
    )
    group = await create_group(
        session=session, name="acl_connection_group", admin_id=group_admin.id
    )
    members: list[MockUser] = []
    for username in (
        "acl_connection_group_member_1",
        "acl_connection_group_member_2",
        "acl_connection_group_member_3",
    ):
        u = await create_user(session, username, is_active=True)
        members.append(MockUser(user=u, auth_token=sign_jwt(u.id, fxtr_settings)))
        session.add(UserGroup(group_id=group.id, user_id=u.id))
    await session.commit()
    connection = await create_connection(
        session=session, name="acl_group_connection", user_id=None, group_id=group.id
    )
    acl = await create_acl(
        session=session,
        object_id=connection.id,
        object_type=ObjectType.CONNECTION,
        user_id=members[0].id,
        rule=Rule.DELETE,
    )
    yield MockConnection(
        connection=connection,
        owner_group=MockGroup(
            group=group,
            admin=MockUser(
                user=group_admin, auth_token=sign_jwt(group_admin.id, fxtr_settings)
            ),
            members=members,
        ),
        owner_user=None,
        acls=[MockAcl(acl=acl, user=members[0], to_object=connection)],
    )
    await session.delete(connection)
    await session.delete(group)
    await session.delete(group_admin)
    for member in members:
        await session.delete(member.user)
    await session.commit()
