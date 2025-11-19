import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue
from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_maintainer_plus_can_create_queue(
    client: AsyncClient,
    session: AsyncSession,
    role_maintainer_plus: UserTestRoles,
    mock_group: MockGroup,
):
    user = mock_group.get_member_of_role(role_maintainer_plus)

    response = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": r"New queue123!\"#$%&'()*+,-./:;<=>?@\[\\\]^_`{|}~",
            "description": "Some interesting description",
            "group_id": mock_group.group.id,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": response.json()["id"],
        "name": r"New queue123!\"#$%&'()*+,-./:;<=>?@\[\\\]^_`{|}~",
        "description": "Some interesting description",
        "group_id": mock_group.group.id,
        "slug": f"{mock_group.group.id}-new_queue123",
    }

    queue = (await session.scalars(select(Queue).filter_by(id=response.json()["id"]))).one()
    assert queue.id == response.json()["id"]
    assert queue.group_id == mock_group.group.id
    assert queue.name == r"New queue123!\"#$%&'()*+,-./:;<=>?@\[\\\]^_`{|}~"
    assert queue.description == "Some interesting description"
    assert queue.slug == f"{mock_group.group.id}-new_queue123"

    await session.delete(queue)
    await session.commit()


async def test_superuser_can_create_queue(
    client: AsyncClient,
    session: AsyncSession,
    mock_group: MockGroup,
    superuser: MockUser,
):
    response = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "name": "New queue",
            "description": "Some interesting description",
            "group_id": mock_group.group.id,
        },
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": response.json()["id"],
        "name": "New queue",
        "description": "Some interesting description",
        "group_id": mock_group.group.id,
        "slug": f"{mock_group.group.id}-new_queue",
    }
    queue = (await session.scalars(select(Queue).filter_by(id=response.json()["id"]))).one()

    assert queue.id == response.json()["id"]
    assert queue.group_id == mock_group.group.id
    assert queue.name == "New queue"
    assert queue.description == "Some interesting description"
    assert queue.slug == f"{mock_group.group.id}-new_queue"

    await session.delete(queue)
    await session.commit()


async def test_developer_or_below_cannot_create_queue(
    client: AsyncClient,
    session: AsyncSession,
    role_developer_or_below: UserTestRoles,
    mock_group: MockGroup,
):
    user = mock_group.get_member_of_role(role_developer_or_below)

    response = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New queue",
            "description": "Some interesting description",
            "group_id": mock_group.id,
        },
    )

    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_other_group_member_cannot_create_queue(
    client: AsyncClient,
    role_developer_plus: UserTestRoles,
    empty_group: MockGroup,
    group: MockGroup,
):
    user = group.get_member_of_role(role_developer_plus)

    response = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New queue",
            "description": "Some interesting description",
            "group_id": empty_group.group.id,
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_groupless_user_cannot_create_queue_error(
    client: AsyncClient,
    simple_user: MockUser,
    empty_group: MockGroup,
):
    response = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "name": "New queue",
            "description": "Some interesting description",
            "group_id": empty_group.group.id,
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_maintainer_plus_cannot_create_queue_with_unknown_group_error(
    client: AsyncClient,
    role_maintainer_plus: UserTestRoles,
    mock_group: MockGroup,
):
    user = mock_group.get_member_of_role(role_maintainer_plus)

    response = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New queue",
            "description": "Some interesting description",
            "group_id": -1,
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_cannot_create_queue_with_unknown_group_error(
    client: AsyncClient,
    superuser: MockUser,
):
    response = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "name": "New queue",
            "description": "Some interesting description",
            "group_id": -1,
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


@pytest.mark.parametrize(
    "name_value,error",
    [
        (
            "очередь",
            {
                "context": {"pattern": r"^[ -~]+$"},
                "input": "очередь",
                "location": ["body", "name"],
                "message": r"String should match pattern '^[ -~]+$'",
                "code": "string_pattern_mismatch",
            },
        ),
        (
            "♥︎♥︎♥︎",
            {
                "context": {"pattern": r"^[ -~]+$"},
                "input": "♥︎♥︎♥︎",
                "location": ["body", "name"],
                "message": r"String should match pattern '^[ -~]+$'",
                "code": "string_pattern_mismatch",
            },
        ),
        (
            "qq",
            {
                "context": {"min_length": 3},
                "input": "qq",
                "location": ["body", "name"],
                "message": "String should have at least 3 characters",
                "code": "string_too_short",
            },
        ),
        (
            "q" * 129,
            {
                "context": {"max_length": 128},
                "input": 129 * "q",
                "location": ["body", "name"],
                "message": "String should have at most 128 characters",
                "code": "string_too_long",
            },
        ),
        (
            None,
            {
                "context": {},
                "input": None,
                "location": ["body", "name"],
                "message": "Input should be a valid string",
                "code": "string_type",
            },
        ),
    ],
)
async def test_maintainer_plus_cannot_create_queue_with_wrong_name(
    client: AsyncClient,
    role_maintainer_plus: UserTestRoles,
    mock_group: MockGroup,
    name_value: str,
    error: dict,
):
    user = mock_group.get_member_of_role(role_maintainer_plus)

    response = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": name_value,
            "description": "Some interesting description",
            "group_id": mock_group.group.id,
        },
    )

    assert response.status_code == 422, response.text
    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [error],
        },
    }


async def test_maintainer_plus_can_not_create_queue_with_duplicate_name_error(
    client: AsyncClient,
    role_maintainer_plus: UserTestRoles,
    mock_group: MockGroup,
    group_queue: Queue,
):
    user = mock_group.get_member_of_role(role_maintainer_plus)

    response = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": group_queue.name,  # duplicated name
            "description": "Some interesting description",
            "group_id": group_queue.group.id,
        },
    )

    assert response.status_code == 409, response.text
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "The queue name already exists in the target group, please specify a new one",
            "details": None,
        },
    }


async def test_maintainer_plus_can_create_queues_with_the_same_name_but_diff_groups(
    client: AsyncClient,
    role_maintainer_plus: UserTestRoles,
    mock_group: MockGroup,
    group: MockGroup,
):
    mock_group_user = mock_group.get_member_of_role(role_maintainer_plus)
    group_user = group.get_member_of_role(role_maintainer_plus)

    queue_1 = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {mock_group_user.token}"},
        json={
            "name": "New queue",
            "description": "Some interesting description",
            "group_id": mock_group.group.id,
        },
    )
    queue_2 = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {group_user.token}"},
        json={
            "name": "New queue",
            "description": "Some interesting description",
            "group_id": group.group.id,
        },
    )
    queue_1_json = queue_1.json()
    queue_2_json = queue_2.json()

    assert queue_1.status_code == 200
    assert queue_1_json == {
        "id": queue_1_json["id"],
        "name": "New queue",
        "description": "Some interesting description",
        "group_id": mock_group.group.id,
        "slug": f"{mock_group.group.id}-new_queue",
    }
    assert queue_2.status_code == 200
    assert queue_2_json == {
        "id": queue_2_json["id"],
        "name": "New queue",
        "description": "Some interesting description",
        "group_id": group.group.id,
        "slug": f"{group.group.id}-new_queue",
    }
    assert queue_1_json["slug"] != queue_2_json["slug"]
