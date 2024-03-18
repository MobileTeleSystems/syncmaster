# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import secrets

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db import Group
from tests.mocks import MockUser

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_simple_user_can_create_group(
    simple_user: MockUser,
    session: AsyncSession,
    client: AsyncClient,
):
    # Arrange
    group_name = f"{secrets.token_hex(5)}"
    group_data = {
        "name": group_name,
        "description": "description of new test group",
    }

    # Act
    result = await client.post(
        "v1/groups",
        json=group_data,
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    # pre assert
    group = (await session.scalars(select(Group).where(Group.name == group_name))).one_or_none()

    # Assert
    assert group
    assert result.status_code == 200
    assert result.json() == {
        "id": group.id,
        "name": group_name,
        "description": "description of new test group",
        "owner_id": simple_user.user.id,
    }


async def test_simple_user_cannot_create_group_twice(
    client: AsyncClient,
    simple_user: MockUser,
):
    # Arrange
    group_data = {
        "name": "test_superuser_cannot_create_group_twice",
        "description": "description of new test group",
        "owner_id": simple_user.id,
    }

    # Act
    result = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json=group_data,
    )

    # Assert
    assert result.status_code == 200

    second_result = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json=group_data,
    )
    assert second_result.status_code == 400
    assert second_result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Group name already taken",
    }


async def test_not_authorized_user_cannot_create_group(
    client: AsyncClient,
    simple_user: MockUser,
):
    # Arrange
    group_data = {
        "name": "new_test_group",
        "description": "description of new test group",
        "owner_id": simple_user.id,
    }

    # Act
    result = await client.post("v1/groups", json=group_data)

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
    assert result.status_code == 401
