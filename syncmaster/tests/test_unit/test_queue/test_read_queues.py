import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockTransfer, MockUser, UserTestRoles

from app.db.models import Queue

pytestmark = [pytest.mark.asyncio]


async def test_group_member_can_read_queues(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,  # another group with queue
    mock_group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = mock_group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.get(
        f"v1/queues?group_id={mock_group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"group_id": mock_group.id},
    )
    # Assert
    assert result.json() == {
        "items": [
            {
                "id": group_queue.id,
                "name": group_queue.name,
                "description": group_queue.description,
                "group_id": mock_group.id,
            },
        ],
        "meta": {
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "page": 1,
            "page_size": 20,
            "pages": 1,
            "previous_page": None,
            "total": 1,
        },
    }
    assert result.status_code == 200


async def test_superuser_can_read_queues(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    superuser: MockUser,
    group_transfer: MockTransfer,  # another group with queue
):
    # Act
    result = await client.get(
        "v1/queues",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": mock_group.id},
    )
    # Assert
    assert result.json() == {
        "items": [
            {
                "id": group_queue.id,
                "name": group_queue.name,
                "description": group_queue.description,
                "group_id": mock_group.id,
            },
        ],
        "meta": {
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "page": 1,
            "page_size": 20,
            "pages": 1,
            "previous_page": None,
            "total": 1,
        },
    }
    assert result.status_code == 200


async def test_other_group_member_cannot_read_queues(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.get(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"group_id": mock_group.id},
    )

    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }


async def test_group_member_cannot_read__unknown_group_queues_error(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    group_transfer: MockTransfer,  # another group with queue
    mock_group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = mock_group.get_member_of_role(role_guest_plus)
    # Act
    result = await client.get(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        params={"group_id": -1},
    )
    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_cannot_read_unknown_group_queues_error(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    superuser: MockUser,
    group_transfer: MockTransfer,  # another group with queue
):
    # Act
    result = await client.get(
        "v1/queues",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={"group_id": -1},
    )
    # Assert
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
