import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue
from tests.mocks import MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_maintainer_plus_can_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    role_maintainer_plus: UserTestRoles,
):
    user = mock_group.get_member_of_role(role_maintainer_plus)

    result = await client.delete(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.status_code == 204, result.json()
    session.expunge_all()
    queue_in_db = await session.get(Queue, group_queue.id)
    assert queue_in_db is None


async def test_superuser_can_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    superuser: MockUser,
):
    result = await client.delete(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 204, result.json()
    session.expunge_all()
    queue_in_db = await session.get(Queue, group_queue.id)
    assert queue_in_db is None


async def test_groupless_user_cannot_delete_queue(
    client: AsyncClient,
    group_queue: Queue,
    simple_user: MockUser,
):
    result = await client.delete(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }
    assert result.status_code == 404, result.json()


async def test_developer_or_below_cannot_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    role_developer_or_below: UserTestRoles,
):
    user = mock_group.get_member_of_role(role_developer_or_below)

    result = await client.delete(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_other_group_member_cannot_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)

    result = await client.delete(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_maintainer_plus_cannot_delete_queue_with_linked_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_maintainer_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    result = await client.delete(
        f"v1/queues/{group_transfer.transfer.queue_id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "The queue has an associated transfers(s). Number of the linked transfers: 1",
            "details": None,
        },
    }
    assert result.status_code == 409, result.json()


async def test_superuser_cannot_delete_queue_with_linked_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
):
    result = await client.delete(
        f"v1/queues/{group_transfer.transfer.queue_id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "The queue has an associated transfers(s). Number of the linked transfers: 1",
            "details": None,
        },
    }
    assert result.status_code == 409, result.json()


async def test_anon_user_cannot_delete_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
):
    result = await client.delete(
        f"v1/queues/{group_queue.id}",
    )
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }
    assert result.status_code == 401, result.json()


async def test_maintainer_plus_cannot_delete_unknown_queue_error(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
):
    user = mock_group.get_member_of_role(UserTestRoles.Owner)

    result = await client.delete(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }


async def test_superuser_cannot_delete_unknown_queue_error(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    mock_group: MockGroup,
    superuser: MockUser,
):
    result = await client.delete(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Queue not found",
            "details": None,
        },
    }
