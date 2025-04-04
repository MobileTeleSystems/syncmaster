from collections.abc import AsyncGenerator, Callable

import pytest_asyncio
from pytest import FixtureRequest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.mocks import MockUser, UserTestRoles
from tests.test_unit.conftest import add_user_to_group
from tests.test_unit.utils import create_group, create_user, create_user_cm


@pytest_asyncio.fixture
async def superuser(session: AsyncSession, access_token_factory) -> AsyncGenerator[MockUser, None]:
    async with create_user_cm(session, username="superuser", is_active=True, is_superuser=True) as user:
        token = access_token_factory(user.id)
        yield MockUser(
            user=user,
            auth_token=token,
            role=UserTestRoles.Superuser,
        )


@pytest_asyncio.fixture
async def simple_user(session: AsyncSession, access_token_factory) -> AsyncGenerator[MockUser, None]:
    async with create_user_cm(session, username="simple_user", is_active=True) as user:
        token = access_token_factory(user.id)
        yield MockUser(
            user=user,
            auth_token=token,
            role=UserTestRoles.Developer,
        )


@pytest_asyncio.fixture(params=[5])
async def simple_users(
    request: FixtureRequest,
    session: AsyncSession,
    access_token_factory: Callable[[int], str],
) -> AsyncGenerator[list[MockUser], None]:
    size = request.param
    users = []
    for i in range(size):
        username = f"simple_user_{i}"
        user = await create_user(
            session=session,
            username=username,
            email=f"{username}@user.user",
            first_name=f"{username}_first",
            middle_name=f"{username}_middle",
            last_name=f"{username}_last",
            is_active=True,
            is_superuser=False,
        )
        token = access_token_factory(user.id)
        mock_user = MockUser(
            user=user,
            auth_token=token,
            role=UserTestRoles.Developer,
        )
        users.append(mock_user)

    await session.commit()

    yield users

    for user in users:
        await session.delete(user)
    await session.commit()


@pytest_asyncio.fixture
async def inactive_user(session: AsyncSession, access_token_factory) -> AsyncGenerator[MockUser, None]:
    async with create_user_cm(session, username="inactive_user") as user:
        access_token_factory(user.id)
        yield MockUser(
            user=user,
            auth_token=access_token_factory(user.id),
            role=UserTestRoles.Developer,
        )


@pytest_asyncio.fixture
async def user_with_many_roles(
    session: AsyncSession,
    simple_user: MockUser,
    access_token_factory,
) -> AsyncGenerator[MockUser, None]:
    user = await create_user(
        session=session,
        username="multi_role_user",
        is_active=True,
    )

    roles = [
        UserTestRoles.Owner,
        UserTestRoles.Maintainer,
        UserTestRoles.Developer,
        UserTestRoles.Guest,
    ]

    groups = []

    for role in roles:
        group = await create_group(
            session=session,
            name=f"group_for_{role}",
            owner_id=user.id if role == UserTestRoles.Owner else simple_user.user.id,
        )

        if role != UserTestRoles.Owner:
            await add_user_to_group(user=user, group_id=group.id, session=session, role=role)
        groups.append(group)

    await session.commit()

    token = access_token_factory(user.id)
    mock_user = MockUser(
        user=user,
        auth_token=token,
    )

    yield mock_user

    for group in groups:
        await session.delete(group)

    await session.delete(user)
    await session.commit()
