import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockQueue, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_superuser_can_update_queue(
    client: AsyncClient,
    superuser: MockUser,
    session: AsyncSession,
    new_queue: MockQueue,
):
    queue_id = new_queue.queue.id

    result = await client.patch(
        f"v1/queues/{queue_id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "name": "New queue name",
            "description": "New description",
            "is_active": False,
        },
    )

    assert result.status_code == 200
    assert result.json() == {
        "id": queue_id,
        "name": "New queue name",
        "description": "New description",
        "is_active": False,
    }


async def test_superuser_can_update_queue_without_is_active(
    client: AsyncClient,
    superuser: MockUser,
    session: AsyncSession,
    new_queue: MockQueue,
):
    queue_id = new_queue.queue.id

    result = await client.patch(
        f"v1/queues/{queue_id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "name": "New queue name",
            "description": "New description",
        },
    )

    assert result.status_code == 200
    assert result.json() == {
        "id": queue_id,
        "name": "New queue name",
        "description": "New description",
        "is_active": True,
    }


async def test_simple_user_can_not_update_queue(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    new_queue: MockQueue,
):
    queue_id = new_queue.queue.id

    result = await client.patch(
        f"v1/queues/{queue_id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={"name": "New queue name", "description": "New description"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_anon_user_can_not_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    new_queue: MockQueue,
):
    queue_id = new_queue.queue.id

    result = await client.patch(
        f"v1/queues/{queue_id}",
        json={"name": "New queue name", "description": "New description"},
    )
    assert result.status_code == 401
    assert result.json() == {
        "message": "Not authenticated",
        "ok": False,
        "status_code": 401,
    }
