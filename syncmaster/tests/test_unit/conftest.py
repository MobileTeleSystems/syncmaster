import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth.utils import sign_jwt
from app.config import Settings
from app.db.models import UserGroup
from tests.test_unit.utils import create_group, create_user, create_user_cm
from tests.utils import MockGroup, MockUser


@pytest_asyncio.fixture
async def superuser(session: AsyncSession, fxtr_settings: Settings):
    async with create_user_cm(
        session, username="superuser", is_active=True, is_superuser=True
    ) as user:
        yield MockUser(user=user, auth_token=sign_jwt(user.id, fxtr_settings))


@pytest_asyncio.fixture
async def simple_user(session: AsyncSession, fxtr_settings: Settings):
    async with create_user_cm(session, username="simple_user", is_active=True) as user:
        yield MockUser(user=user, auth_token=sign_jwt(user.id, fxtr_settings))


@pytest_asyncio.fixture
async def inactive_user(session: AsyncSession, fxtr_settings: Settings):
    async with create_user_cm(session, username="inactive_user") as user:
        yield MockUser(user=user, auth_token=sign_jwt(user.id, fxtr_settings))


@pytest_asyncio.fixture
async def deleted_user(session: AsyncSession, fxtr_settings: Settings):
    async with create_user_cm(
        session, username="deleted_user", is_deleted=True
    ) as user:
        yield MockUser(user=user, auth_token=sign_jwt(user.id, fxtr_settings))


@pytest_asyncio.fixture
async def empty_group(session: AsyncSession, fxtr_settings) -> MockGroup:
    admin = await create_user(
        session=session, username="empty_group_admin", is_active=True
    )
    group = await create_group(session=session, name="empty_group", admin_id=admin.id)
    yield MockGroup(
        group=group,
        admin=MockUser(user=admin, auth_token=sign_jwt(admin.id, fxtr_settings)),
        members=[],
    )
    await session.delete(group)
    await session.delete(admin)
    await session.commit()


@pytest_asyncio.fixture
async def not_empty_group(session: AsyncSession, fxtr_settings) -> MockGroup:
    admin = await create_user(
        session=session, username="notempty_group_admin", is_active=True
    )
    group = await create_group(
        session=session, name="notempty_group", admin_id=admin.id
    )
    members: list[MockUser] = []
    for username in ("not_empty_member_1", "not_empty_member_2", "not_empty_member_3"):
        u = await create_user(session, username, is_active=True)
        members.append(MockUser(user=u, auth_token=sign_jwt(u.id, fxtr_settings)))
        session.add(UserGroup(group_id=group.id, user_id=u.id))
    await session.commit()
    yield MockGroup(
        group=group,
        admin=MockUser(user=admin, auth_token=sign_jwt(admin.id, fxtr_settings)),
        members=members,
    )
    await session.delete(group)
    await session.delete(admin)
    for member in members:
        await session.delete(member.user)
    await session.commit()
