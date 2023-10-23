import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_unit.utils import create_queue
from tests.utils import MockQueue, MockUser

pytestmark = [pytest.mark.asyncio]


async def test_read_queues(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    new_queue: MockQueue,
    event_loop,
    request,
):
    queue = await create_queue(
        session=session,
        name="test_read_queues",
        is_active=True,
    )

    def finalizer() -> None:
        async def async_finalizer() -> None:
            await session.delete(queue)
            await session.commit()

        event_loop.run_until_complete(async_finalizer())

    request.addfinalizer(finalizer)

    result = await client.get(
        f"v1/queues",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "items": [
            {
                "id": new_queue.queue.id,
                "name": new_queue.queue.name,
                "description": "",
                "is_active": True,
            },
            {
                "id": queue.id,
                "name": queue.name,
                "description": "",
                "is_active": True,
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
            "total": 2,
        },
    }
