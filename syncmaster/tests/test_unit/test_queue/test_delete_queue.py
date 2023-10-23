import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, MockQueue, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_delete_queue_with_linked_connection_error(
    client: AsyncClient,
    session: AsyncSession,
    group_queue_connection: MockConnection,
    superuser: MockConnection,
):
    queue_id = group_queue_connection.connection.queue.id

    result = await client.delete(
        f"v1/queues/{queue_id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 409
    assert result.json() == {
        "ok": False,
        "status_code": 409,
        "message": "The queue has an associated connection(s). Number of the connected connections: 1",
    }


async def test_anon_user_cannot_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    new_queue: MockQueue,
):
    queue_id = new_queue.queue.id

    result = await client.delete(
        f"v1/queues/{queue_id}",
    )
    assert result.status_code == 401
    assert result.json() == {
        "message": "Not authenticated",
        "ok": False,
        "status_code": 401,
    }


async def test_simple_user_cannot_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    new_queue: MockQueue,
    simple_user: MockUser,
):
    queue_id = new_queue.queue.id

    result = await client.delete(
        f"v1/queues/{queue_id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }


async def test_superuser_can_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    new_queue: MockQueue,
    superuser: MockUser,
):
    queue_id = new_queue.queue.id

    result = await client.delete(
        f"v1/queues/{queue_id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "message": "Queue was deleted",
        "ok": True,
        "status_code": 200,
    }
