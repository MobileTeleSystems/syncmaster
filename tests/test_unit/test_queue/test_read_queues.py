import random
import string

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue
from tests.mocks import MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


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
                "slug": f"{mock_group.id}-{group_queue.name}",
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
                "slug": f"{mock_group.id}-{group_queue.name}",
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
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
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
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
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
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


@pytest.mark.parametrize(
    "search_value_extractor",
    [
        lambda queue: queue.name,
        lambda queue: "_".join(queue.name.split("_")[:1]),
        lambda queue: "_".join(queue.name.split("_")[:2]),
        lambda queue: "_".join(queue.name.split("_")[-1:]),
    ],
    ids=[
        "search_by_name_full_match",
        "search_by_name_first_token",
        "search_by_name_two_tokens",
        "search_by_name_last_token",
    ],
)
async def test_search_queues_with_query(
    client: AsyncClient,
    group_queue: Queue,
    mock_group: MockGroup,
    superuser: MockUser,
    search_value_extractor,
):
    search_query = search_value_extractor(group_queue)

    result = await client.get(
        "v1/queues",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={
            "group_id": mock_group.id,
            "search_query": search_query,
        },
    )

    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 1,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": group_queue.id,
                "name": group_queue.name,
                "description": group_queue.description,
                "group_id": mock_group.id,
                "slug": f"{mock_group.id}-{group_queue.name}",
            },
        ],
    }
    assert result.status_code == 200


async def test_search_queues_with_nonexistent_query(
    client: AsyncClient,
    superuser: MockUser,
    mock_group: MockGroup,
):
    random_search_query = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))

    result = await client.get(
        "v1/queues",
        headers={"Authorization": f"Bearer {superuser.token}"},
        params={
            "group_id": mock_group.id,
            "search_query": random_search_query,
        },
    )

    assert result.status_code == 200
    assert result.json()["items"] == []
