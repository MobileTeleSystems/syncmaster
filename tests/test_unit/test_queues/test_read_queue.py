import pytest
from httpx import AsyncClient

from syncmaster.db.models import Queue
from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_group_member_can_read_queue(
    client: AsyncClient,
    group_queue: Queue,
    mock_group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = mock_group.get_member_of_role(role_guest_plus)

    response = await client.get(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": group_queue.id,
        "name": group_queue.name,
        "description": group_queue.description,
        "group_id": group_queue.group_id,
        "slug": f"{group_queue.group_id}-{group_queue.name}",
    }


async def test_superuser_can_read_queue(
    client: AsyncClient,
    group_queue: Queue,
    superuser: MockUser,
):
    response = await client.get(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": group_queue.id,
        "name": group_queue.name,
        "description": group_queue.description,
        "group_id": group_queue.group_id,
        "slug": f"{group_queue.group_id}-{group_queue.name}",
    }


async def test_groupless_user_cannot_read_queue(
    client: AsyncClient,
    group_queue: Queue,
    mock_group: MockGroup,
    simple_user: MockUser,
):
    response = await client.get(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_other_group_guest_plus_cannot_read_queue(
    client: AsyncClient,
    group_queue: Queue,
    mock_group: MockGroup,
    role_guest_plus: UserTestRoles,
    group: MockGroup,
):
    user = group.get_member_of_role(role_guest_plus)

    response = await client.get(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_anon_user_cannot_read_queue_error(
    client: AsyncClient,
    group_queue: Queue,
):
    response = await client.get(
        f"v1/queues/{group_queue.id}",
    )
    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_group_member_cannot_read_unknown_queue_error(
    client: AsyncClient,
    mock_group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = mock_group.get_member_of_role(role_guest_plus)

    response = await client.get(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_superuser_cannot_read_unknow_queue_error(
    client: AsyncClient,
    group_queue: Queue,
    superuser: MockUser,
):
    response = await client.get(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }
