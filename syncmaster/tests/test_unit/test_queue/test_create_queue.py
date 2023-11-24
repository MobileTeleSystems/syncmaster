import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockUser, TestUserRoles

from app.db.models import Queue

pytestmark = [pytest.mark.asyncio]


async def test_maintainer_plus_can_create_queue(
    client: AsyncClient,
    session: AsyncSession,
    role_maintainer_plus: TestUserRoles,
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


async def test_user_or_below_cannot_create_queue(
    client: AsyncClient,
    session: AsyncSession,
    role_user_or_below: TestUserRoles,
    mock_group: MockGroup,
):
    # Arrange
    user = mock_group.get_member_of_role(role_user_or_below)

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
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }


async def test_other_group_member_cannot_create_queue(
    client: AsyncClient,
    role_user_plus: TestUserRoles,
    empty_group: MockGroup,
    group: MockGroup,
):
    # Arrange
    user = group.get_member_of_role(role_user_plus)

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
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
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
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


async def test_maintainer_plus_cannot_create_queue_with_unknown_group_error(
    client: AsyncClient,
    role_maintainer_plus: TestUserRoles,
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
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
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
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }


@pytest.mark.parametrize("name", ["очередь", "Queue name", "♥︎", "q" * 129])
async def test_maintainer_plus_cannot_create_queue_with_wrong_name(
    client: AsyncClient,
    session: AsyncSession,
    role_maintainer_plus: TestUserRoles,
    mock_group: MockGroup,
    name: str,
):
    # Arrange
    user = mock_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.post(
        "v1/queues",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": name,
            "description": "Some interesting description",
            "group_id": mock_group.group.id,
        },
    )

    # Assert
    assert result.json()["detail"][0]["loc"] == ["body", "name"]
