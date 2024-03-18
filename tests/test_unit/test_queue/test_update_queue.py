# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db import Queue
from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_maintainer_plus_can_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    role_maintainer_plus: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
):
    # Arrange
    user = mock_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "description": "New description",
        },
    )

    # Assert
    assert result.json() == {
        "id": group_queue.id,
        "name": group_queue.name,
        "description": "New description",
        "group_id": group_queue.group_id,
    }
    assert result.status_code == 200

    queue = await session.get(Queue, group_queue.id)
    await session.refresh(queue)

    assert result.json() == {
        "id": queue.id,
        "name": queue.name,
        "description": queue.description,
        "group_id": queue.group_id,
    }


async def test_superuser_can_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    superuser: MockUser,
):
    # Act
    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "description": "New description",
        },
    )

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "id": group_queue.id,
        "name": group_queue.name,
        "description": "New description",
        "group_id": group_queue.group_id,
    }

    queue = await session.get(Queue, group_queue.id)
    await session.refresh(queue)

    assert result.json() == {
        "id": queue.id,
        "name": queue.name,
        "description": queue.description,
        "group_id": queue.group_id,
    }


async def test_groupless_user_cannot_update_queue(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    group_queue: Queue,
):
    # Act
    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"description": "New description"},
    )
    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_anon_user_cannot_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
):
    # Act
    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        json={"description": "New description"},
    )
    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "message": "Not authenticated",
        "ok": False,
        "status_code": 401,
    }


async def test_developer_or_below_cannot_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    role_developer_or_below: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
):
    # Arrange
    user = mock_group.get_member_of_role(role_developer_or_below)

    # Act
    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "description": "New description",
        },
    )

    # Assert
    assert result.json() == {
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }
    assert result.status_code == 403


async def test_other_group_member_cannot_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    group: MockGroup,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_developer_plus)
    # Act
    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"description": "New description"},
    )
    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }


async def test_maintainer_plus_cannot_update_unknown_queue_error(
    client: AsyncClient,
    session: AsyncSession,
    role_maintainer_plus: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
):
    # Arrange
    user = mock_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.patch(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "description": "New description",
        },
    )

    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_superuser_cannot_update_unknown_queue_error(
    client: AsyncClient,
    session: AsyncSession,
    superuser: MockUser,
    group_queue: Queue,
    mock_group: MockGroup,
):
    # Act
    result = await client.patch(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "description": "New description",
        },
    )

    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404
