import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Queue
from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_maintainer_plus_can_create_queue(
    client: AsyncClient,
    session: AsyncSession,
    role_maintainer_plus: UserTestRoles,
    mock_group: MockGroup,
):
    # Arrange
    user = mock_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New_queue",
            "description": "Some interesting description",
            "group_id": mock_group.group.id,
        },
    )

    # Assert
    assert result.json() == {
        "id": result.json()["id"],
        "name": "New_queue",
        "description": "Some interesting description",
        "group_id": mock_group.group.id,
    }
    assert result.status_code == 200
    queue = (await session.scalars(select(Queue).filter_by(id=result.json()["id"]))).one()

    assert queue.id == result.json()["id"]
    assert queue.group_id == mock_group.group.id
    assert queue.name == "New_queue"
    assert queue.description == "Some interesting description"

    await session.delete(queue)
    await session.commit()


async def test_superuser_can_create_queue(
    client: AsyncClient,
    session: AsyncSession,
    mock_group: MockGroup,
    superuser: MockUser,
):
    # Act
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "name": "New_queue",
            "description": "Some interesting description",
            "group_id": mock_group.group.id,
        },
    )

    # Assert
    assert result.json() == {
        "id": result.json()["id"],
        "name": "New_queue",
        "description": "Some interesting description",
        "group_id": mock_group.group.id,
    }
    assert result.status_code == 200
    queue = (await session.scalars(select(Queue).filter_by(id=result.json()["id"]))).one()

    assert queue.id == result.json()["id"]
    assert queue.group_id == mock_group.group.id
    assert queue.name == "New_queue"
    assert queue.description == "Some interesting description"

    await session.delete(queue)
    await session.commit()


async def test_developer_or_below_cannot_create_queue(
    client: AsyncClient,
    session: AsyncSession,
    role_developer_or_below: UserTestRoles,
    mock_group: MockGroup,
):
    # Arrange
    user = mock_group.get_member_of_role(role_developer_or_below)

    # Act
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New_queue",
            "description": "Some interesting description",
            "group_id": mock_group.id,
        },
    )

    # Assert
    assert result.json() == {
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
    # Arrange
    user = group.get_member_of_role(role_developer_plus)

    # Act
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New_queue",
            "description": "Some interesting description",
            "group_id": empty_group.group.id,
        },
    )

    # Assert
    assert result.json() == {
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
    session: AsyncSession,
):
    # Act
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "name": "New_queue",
            "description": "Some interesting description",
            "group_id": empty_group.group.id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_maintainer_plus_cannot_create_queue_with_unknown_group_error(
    client: AsyncClient,
    role_maintainer_plus: UserTestRoles,
    mock_group: MockGroup,
):
    # Arrange
    user = mock_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": "New_queue",
            "description": "Some interesting description",
            "group_id": -1,
        },
    )

    # Assert
    assert result.json() == {
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
    # Act
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "name": "New_queue",
            "description": "Some interesting description",
            "group_id": -1,
        },
    )

    # Assert
    assert result.json() == {
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
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "context": {"pattern": "^[-_a-zA-Z0-9]+$"},
                            "input": "очередь",
                            "location": ["body", "name"],
                            "message": "String should match pattern '^[-_a-zA-Z0-9]+$'",
                            "code": "string_pattern_mismatch",
                        },
                    ],
                },
            },
        ),
        (
            "Queue name",
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "context": {"pattern": "^[-_a-zA-Z0-9]+$"},
                            "input": "Queue name",
                            "location": ["body", "name"],
                            "message": "String should match pattern '^[-_a-zA-Z0-9]+$'",
                            "code": "string_pattern_mismatch",
                        },
                    ],
                },
            },
        ),
        (
            "♥︎",
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "context": {"pattern": "^[-_a-zA-Z0-9]+$"},
                            "input": "♥︎",
                            "location": ["body", "name"],
                            "message": "String should match pattern '^[-_a-zA-Z0-9]+$'",
                            "code": "string_pattern_mismatch",
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
            "",
            {
                "error": {
                    "code": "invalid_request",
                    "message": "Invalid request",
                    "details": [
                        {
                            "context": {"pattern": "^[-_a-zA-Z0-9]+$"},
                            "input": "",
                            "location": ["body", "name"],
                            "message": "String should match pattern '^[-_a-zA-Z0-9]+$'",
                            "code": "string_pattern_mismatch",
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
async def test_maintainer_plus_cannot_create_queue_with_wrong_name(
    client: AsyncClient,
    session: AsyncSession,
    role_maintainer_plus: UserTestRoles,
    mock_group: MockGroup,
    name_value: str,
    error: dict,
):
    # Arrange
    user = mock_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": name_value,
            "description": "Some interesting description",
            "group_id": mock_group.group.id,
        },
    )

    # Assert
    assert result.json() == error


async def test_maintainer_plus_can_not_create_queue_with_duplicate_name_error(
    client: AsyncClient,
    session: AsyncSession,
    role_maintainer_plus: UserTestRoles,
    mock_group: MockGroup,
    group_queue: Queue,
):
    # Arrange
    user = mock_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": group_queue.name,  # duplicated name
            "description": "Some interesting description",
            "group_id": group_queue.group.id,
        },
    )

    # Assert
    assert result.status_code == 409
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "The queue name already exists in the target group, please specify a new one",
            "details": None,
        },
    }
