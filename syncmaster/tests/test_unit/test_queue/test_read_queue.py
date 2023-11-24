import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockUser, TestUserRoles

from app.db.models import Queue

pytestmark = [pytest.mark.asyncio]


async def test_group_member_can_read_queue(
    client: AsyncClient,
    group_queue: Queue,
    mock_group: MockGroup,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    user = mock_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "id": group_queue.id,
        "name": group_queue.name,
        "description": group_queue.description,
        "group_id": group_queue.group_id,
    }
    assert result.status_code == 200


async def test_superuser_can_read_queue(
    client: AsyncClient,
    group_queue: Queue,
    superuser: MockUser,
):
    # Act
    result = await client.get(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.json() == {
        "id": group_queue.id,
        "name": group_queue.name,
        "description": group_queue.description,
        "group_id": group_queue.group_id,
    }
    assert result.status_code == 200


async def test_groupless_user_cannot_read_queue(
    client: AsyncClient,
    group_queue: Queue,
    mock_group: MockGroup,
    simple_user: MockUser,
):
    # Act
    result = await client.get(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }


async def test_other_group_guest_plus_cannot_read_queue(
    client: AsyncClient,
    group_queue: Queue,
    mock_group: MockGroup,
    role_guest_plus: TestUserRoles,
    group: MockGroup,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }


async def test_anon_user_cannot_read_queue_error(
    client: AsyncClient,
    group_queue: Queue,
):
    # Act
    result = await client.get(
        f"v1/queues/{group_queue.id}",
    )
    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
    assert result.status_code == 401


async def test_group_member_cannot_read_unknown_queue_error(
    client: AsyncClient,
    mock_group: MockGroup,
    role_guest_plus: TestUserRoles,
):
    # Arrange
    user = mock_group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.get(
        f"v1/queues/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_cannot_read_unknow_queue_error(
    client: AsyncClient,
    group_queue: Queue,
    superuser: MockUser,
):
    # Act
    result = await client.get(
        f"v1/queues/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "Queue not found",
        "ok": False,
        "status_code": 404,
    }
