import secrets

import pytest_asyncio
from pytest import FixtureRequest
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockUser, UserTestRoles
from tests.test_unit.utils import create_group, create_queue, create_user


@pytest_asyncio.fixture
async def group_owner(
    settings: Settings,
    session: AsyncSession,
    access_token_factory,
):
    user = await create_user(
        session=session,
        username=secrets.token_hex(5),
        is_active=True,
    )

    token = access_token_factory(user.id)
    yield MockUser(
        user=user,
        auth_token=token,
        role=UserTestRoles.Owner,
    )

    await session.delete(user)
    await session.commit()


@pytest_asyncio.fixture
async def group(
    session: AsyncSession,
    group_owner: MockUser,
):
    result = await create_group(session=session, name=secrets.token_hex(5), owner_id=group_owner.user.id)
    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture(params=["test_queue"])
async def queue(
    request: FixtureRequest,
    session: AsyncSession,
    group: Group,
):
    result = await create_queue(
        session=session,
        name=request.param,
        group_id=group.id,
        slug=request.param,
    )
    yield result
    await session.delete(result)
    await session.commit()
