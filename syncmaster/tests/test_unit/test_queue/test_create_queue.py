import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockUser

from app.db.models import Queue

pytestmark = [pytest.mark.asyncio]


async def test_superuser_can_create_queue(
    client: AsyncClient,
    superuser: MockUser,
    session: AsyncSession,
):
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "name": "New queue",
            "description": "Some interesting description",
        },
    )

    created_queue_id = result.json()["id"]
    assert result.status_code == 200
    assert result.json() == {
        "id": created_queue_id,
        "name": "New queue",
        "description": "Some interesting description",
        "is_active": True,
    }
    queue = (await session.scalars(select(Queue).filter_by(id=created_queue_id))).one()

    await session.delete(queue)
    await session.commit()


async def test_simple_user_can_not_create_queue_error(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
):
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "name": "New queue",
            "description": "Some interesting description",
        },
    )

    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }
