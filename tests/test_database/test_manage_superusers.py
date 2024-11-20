from __future__ import annotations

import logging

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.backend.scripts.manage_superusers import (
    add_superusers,
    list_superusers,
    remove_superusers,
)
from syncmaster.db.models.user import User
from tests.mocks import MockUser

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


@pytest.mark.parametrize("simple_users", [10], indirect=True)
async def test_add_superusers(caplog, session: AsyncSession, simple_users: list[MockUser]):
    expected_superusers = [user.username for user in simple_users[:5]]
    expected_not_superusers = [user.username for user in simple_users[5:]]

    with caplog.at_level(logging.INFO):
        await add_superusers(session, expected_superusers)

    for username in expected_superusers:
        assert repr(username) in caplog.text

    for username in expected_not_superusers:
        assert repr(username) not in caplog.text

    superusers_query = select(User).where(User.username.in_(expected_superusers))
    superusers_query_result = await session.execute(superusers_query)
    superusers = superusers_query_result.scalars().all()

    assert set(expected_superusers) == {user.username for user in superusers}
    for superuser in superusers:
        assert superuser.is_superuser

    not_superusers_query = select(User).where(User.username.in_(expected_not_superusers))
    not_superusers_query_result = await session.execute(not_superusers_query)
    not_superusers = not_superusers_query_result.scalars().all()

    assert set(expected_not_superusers) == {user.username for user in not_superusers}
    for user in not_superusers:
        assert not user.is_superuser


@pytest.mark.parametrize("simple_users", [10], indirect=True)
async def test_remove_superusers(caplog, session: AsyncSession, simple_users: list[MockUser]):
    # users 0-4 will be superusers, 5-10 will not
    to_create = [user.username for user in simple_users[:5]]
    to_delete = [user.username for user in simple_users[5:]]

    expected_superusers = [user.username for user in simple_users[:5]]
    expected_not_superusers = [user.username for user in simple_users[5:]]

    await add_superusers(session, to_create)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        await remove_superusers(session, to_delete)

    for username in expected_superusers:
        assert repr(username) not in caplog.text

    for username in expected_not_superusers:
        assert repr(username) in caplog.text

    superusers_query = select(User).where(User.username.in_(expected_superusers))
    superusers_query_result = await session.execute(superusers_query)
    superusers = superusers_query_result.scalars().all()

    assert set(expected_superusers) == {user.username for user in superusers}
    for superuser in superusers:
        assert superuser.is_superuser

    not_superusers_query = select(User).where(User.username.in_(expected_not_superusers))
    not_superusers_query_result = await session.execute(not_superusers_query)
    not_superusers = not_superusers_query_result.scalars().all()

    assert set(expected_not_superusers) == {user.username for user in not_superusers}
    for user in not_superusers:
        assert not user.is_superuser


@pytest.mark.parametrize("simple_users", [10], indirect=True)
async def test_list_superusers(caplog, session: AsyncSession, simple_users: list[MockUser]):
    expected_superusers = [user.username for user in simple_users[:5]]
    expected_not_superusers = [user.username for user in simple_users[5:]]

    await add_superusers(session, expected_superusers)

    caplog.clear()
    with caplog.at_level(logging.INFO):
        await list_superusers(session)

    for username in expected_superusers:
        assert repr(username) in caplog.text

    for username in expected_not_superusers:
        assert repr(username) not in caplog.text
