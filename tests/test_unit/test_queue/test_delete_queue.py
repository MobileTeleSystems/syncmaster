# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db import Queue
from tests.utils import MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_maintainer_plus_can_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    role_maintainer_plus: UserTestRoles,
):
    # Arrange
    user = mock_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.delete(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "message": "Queue was deleted",
        "ok": True,
        "status_code": 200,
    }
    assert result.status_code == 200

    queue = await session.get(Queue, group_queue.id)
    await session.refresh(queue)

    assert queue.is_deleted


async def test_superuser_can_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    superuser: MockUser,
):
    # Act
    result = await client.delete(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    assert result.json() == {
        "message": "Queue was deleted",
        "ok": True,
        "status_code": 200,
    }
    assert result.status_code == 200

    queue = await session.get(Queue, group_queue.id)
    await session.refresh(queue)

    assert queue.is_deleted


async def test_groupless_user_cannot_delete_queue(
    client: AsyncClient,
    group_queue: Queue,
    simple_user: MockUser,
):
    # Act
    result = await client.delete(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_developer_or_below_cannot_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    role_developer_or_below: UserTestRoles,
):
    # Arrange
    user = mock_group.get_member_of_role(role_developer_or_below)

    # Act
    result = await client.delete(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }


async def test_other_group_member_cannot_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.delete(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }


async def test_maintainer_plus_cannot_delete_queue_with_linked_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_maintainer_plus: UserTestRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.delete(
        f"v1/queues/{group_transfer.transfer.queue_id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "The queue has an associated transfers(s). Number of the linked transfers: 1",
        "ok": False,
        "status_code": 409,
    }
    assert result.status_code == 409


async def test_superuser_cannot_delete_queue_with_linked_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
):
    # Act
    result = await client.delete(
        f"v1/queues/{group_transfer.transfer.queue_id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "The queue has an associated transfers(s). Number of the linked transfers: 1",
        "ok": False,
        "status_code": 409,
    }
    assert result.status_code == 409


async def test_anon_user_cannot_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
):
    # Act
    result = await client.delete(
        f"v1/queues/{group_queue.id}",
    )
    # Assert
    assert result.json() == {
        "message": "Not authenticated",
        "ok": False,
        "status_code": 401,
    }
    assert result.status_code == 401


async def test_maintainer_plus_cannot_delete_unknown_queue_error(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
):
    # Arrange
    user = mock_group.get_member_of_role(UserTestRoles.Owner)

    # Act
    result = await client.delete(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_cannot_delete_unknown_queue_error(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    superuser: MockUser,
):
    # Act
    result = await client.delete(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }
