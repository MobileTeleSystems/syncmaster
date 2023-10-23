import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockQueue, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_simple_user_can_read_queue(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    new_queue: MockQueue,
):
    queue_id = new_queue.queue.id

    result = await client.get(
        f"v1/queues/{queue_id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert result.status_code == 200
    assert result.json() == {
        "id": queue_id,
        "name": new_queue.queue.name,
        "description": "",
        "is_active": True,
    }


async def test_anon_user_can_not_read_queue_error(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    new_queue: MockQueue,
):
    queue_id = new_queue.queue.id

    result = await client.get(
        f"v1/queues/{queue_id}",
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
