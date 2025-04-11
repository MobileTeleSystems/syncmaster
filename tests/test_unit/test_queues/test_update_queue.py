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

    result = await client.put(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New  awesome_queue-123",
            "description": "New description",
        },
    )

    assert result.json() == {
        "id": group_queue.id,
        "name": "New  awesome_queue-123",
        "description": "New description",
        "group_id": group_queue.group_id,
        "slug": group_queue.slug,
    }
    assert result.status_code == 200, result.json()

    queue = await session.get(Queue, group_queue.id)
    await session.refresh(queue)
    assert queue.name == "New  awesome_queue-123"
    assert queue.description == "New description"
    assert queue.slug == group_queue.slug


async def test_superuser_can_update_queue(
    client: AsyncClient,
    session: AsyncSession,
    group_queue: Queue,
    superuser: MockUser,
):
    result = await client.put(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "name": "New  awesome_queue-123",
            "description": "New description",
        },
    )

    assert result.status_code == 200, result.json()
    assert result.json() == {
        "id": group_queue.id,
        "name": "New  awesome_queue-123",
        "description": "New description",
        "group_id": group_queue.group_id,
        "slug": group_queue.slug,
    }

    queue = await session.get(Queue, group_queue.id)
    await session.refresh(queue)
    assert queue.name == "New  awesome_queue-123"
    assert queue.description == "New description"
    assert queue.slug == group_queue.slug


async def test_groupless_user_cannot_update_queue(
    client: AsyncClient,
    simple_user: MockUser,
    group_queue: Queue,
):
    result = await client.put(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "name": "New  awesome_queue-123",
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


async def test_anon_user_cannot_update_queue(
    client: AsyncClient,
    group_queue: Queue,
):
    result = await client.put(
        f"v1/queues/{group_queue.id}",
        json={
            "name": "New  awesome_queue-123",
            "description": "New description",
        },
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
    role_developer_or_below: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
):
    user = mock_group.get_member_of_role(role_developer_or_below)

    result = await client.put(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New  awesome_queue-123",
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
    group_queue: Queue,
    group: MockGroup,
    role_developer_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_developer_plus)
    result = await client.put(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New  awesome_queue-123",
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


async def test_maintainer_plus_cannot_update_unknown_queue_error(
    client: AsyncClient,
    role_maintainer_plus: UserTestRoles,
    mock_group: MockGroup,
):
    user = mock_group.get_member_of_role(role_maintainer_plus)

    result = await client.put(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New  awesome_queue-123",
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
    superuser: MockUser,
):
    result = await client.put(
        "v1/queues/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "name": "New  awesome_queue-123",
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


@pytest.mark.parametrize(
    "name_value,error",
    [
        (
            "очередь",
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "context": {"pattern": "^[-_ a-zA-Z0-9]+$"},
                            "input": "очередь",
                            "location": ["body", "name"],
                            "message": "String should match pattern '^[-_ a-zA-Z0-9]+$'",
                            "code": "string_pattern_mismatch",
                        },
                    ],
                },
            },
        ),
        (
            "♥︎♥︎♥︎",
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "context": {"pattern": "^[-_ a-zA-Z0-9]+$"},
                            "input": "♥︎♥︎♥︎",
                            "location": ["body", "name"],
                            "message": "String should match pattern '^[-_ a-zA-Z0-9]+$'",
                            "code": "string_pattern_mismatch",
                        },
                    ],
                },
            },
        ),
        (
            "qq",
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "context": {"min_length": 3},
                            "input": "qq",
                            "location": ["body", "name"],
                            "message": "String should have at least 3 characters",
                            "code": "string_too_short",
                        },
                    ],
                },
            },
        ),
        (
            "q" * 129,
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "context": {"max_length": 128},
                            "input": 129 * "q",
                            "location": ["body", "name"],
                            "message": "String should have at most 128 characters",
                            "code": "string_too_long",
                        },
                    ],
                },
            },
        ),
        (
            None,
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "context": {},
                            "input": None,
                            "location": ["body", "name"],
                            "message": "Input should be a valid string",
                            "code": "string_type",
                        },
                    ],
                },
            },
        ),
    ],
)
async def test_maintainer_plus_cannot_update_queue_with_wrong_name(
    client: AsyncClient,
    role_maintainer_plus: UserTestRoles,
    group_queue: Queue,
    mock_group: MockGroup,
    name_value: str,
    error: dict,
):
    user = mock_group.get_member_of_role(role_maintainer_plus)

    result = await client.put(
        f"v1/queues/{group_queue.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": name_value,
            "description": "Some interesting description",
        },
    )

    assert result.status_code == 422, result.json()
    assert result.json() == error
