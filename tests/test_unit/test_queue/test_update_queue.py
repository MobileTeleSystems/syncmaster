import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue
from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_maintainer_plus_can_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    role_maintainer_plus: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
):
    user = mock_group.get_member_of_role(role_maintainer_plus)

    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "description": "New description",
        },
    )

    assert result.json() == {
        "id": group_queue.id,
        "name": group_queue.name,
        "description": "New description",
        "group_id": group_queue.group_id,
        "slug": f"{group_queue.group_id}-{group_queue.name}",
    }
    assert result.status_code == 200, result.json()

    queue = await session.get(Queue, group_queue.id)
    await session.refresh(queue)
    assert queue.description == "New description"


async def test_superuser_can_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    superuser: MockUser,
):
    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "description": "New description",
        },
    )

    assert result.status_code == 200, result.json()
    assert result.json() == {
        "id": group_queue.id,
        "name": group_queue.name,
        "description": "New description",
        "group_id": group_queue.group_id,
        "slug": f"{group_queue.group_id}-{group_queue.name}",
    }

    queue = await session.get(Queue, group_queue.id)
    await session.refresh(queue)
    assert queue.description == "New description"


async def test_groupless_user_cannot_update_queue(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    group_queue: Queue,
):
    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"description": "New description"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_anon_user_cannot_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
):
    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        json={"description": "New description"},
    )
    assert result.status_code == 401, result.json()
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_developer_or_below_cannot_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    role_developer_or_below: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
):
    user = mock_group.get_member_of_role(role_developer_or_below)

    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "description": "New description",
        },
    )

    assert result.status_code == 403, result.json()
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_other_group_member_cannot_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    group: MockGroup,
    role_developer_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_developer_plus)
    result = await client.patch(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"description": "New description"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_maintainer_plus_cannot_update_unknown_queue_error(
    client: AsyncClient,
    session: AsyncSession,
    role_maintainer_plus: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
):
    user = mock_group.get_member_of_role(role_maintainer_plus)

    result = await client.patch(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "description": "New description",
        },
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_superuser_cannot_update_unknown_queue_error(
    client: AsyncClient,
    session: AsyncSession,
    superuser: MockUser,
    group_queue: Queue,
    mock_group: MockGroup,
):
    result = await client.patch(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "description": "New description",
        },
    )

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }
