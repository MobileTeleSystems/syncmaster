import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockUser

from app.db.models import Group

pytestmark = [pytest.mark.asyncio]


async def test_only_superuser_can_create_group(
    client: AsyncClient,
    session: AsyncSession,
    simple_user: MockUser,
    superuser: MockUser,
):
    # Arrange
    group_data = {
        "name": "new_test_group",
        "description": "description of new test group",
        "owner_id": simple_user.id,
    }

    group = (await session.scalars(select(Group).where(Group.name == group_data["name"]))).one_or_none()
    assert not group

    # Act
    result = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )

    # Assert
    group = (await session.scalars(select(Group).where(Group.name == group_data["name"]))).one()
    assert result.json() == {
        "id": group.id,
        "name": group_data["name"],
        "owner_id": group_data["owner_id"],
        "description": group_data["description"],
    }
    assert result.status_code == 200


async def test_not_superuser_cannot_create_group(
    client: AsyncClient,
    simple_user: MockUser,
):
    # Arrange
    group_data = {
        "name": "new_test_group",
        "description": "description of new test group",
        "owner_id": simple_user.id,
    }

    # Act
    result = await client.post(
        "v1/groups",
        json=group_data,
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }
    assert result.status_code == 403


async def test_superuser_cannot_create_group_twice(
    client: AsyncClient,
    simple_user: MockUser,
    superuser: MockUser,
):
    # Arrange
    group_data = {
        "name": "test_superuser_cannot_create_group_twice",
        "description": "description of new test group",
        "owner_id": simple_user.id,
    }

    # Act
    result = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )

    # Assert
    assert result.status_code == 200

    second_result = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )
    assert second_result.status_code == 400
    assert second_result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Group name already taken",
    }


async def test_not_authorized_user_cannot_create_group(
    client: AsyncClient,
    simple_user: MockUser,
):
    # Arrange
    group_data = {
        "name": "new_test_group",
        "description": "description of new test group",
        "owner_id": simple_user.id,
    }

    # Act
    result = await client.post("v1/groups", json=group_data)

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
    assert result.status_code == 401


async def test_superuser_cannot_create_group_with_incorrect_owner_id_error(
    client: AsyncClient,
    superuser: MockUser,
):
    # Arrange
    group_data = {
        "name": "new_another_group",
        "description": "description of new test group",
        "owner_id": -123,
    }

    # Act
    result = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Admin not found",
    }
    assert result.status_code == 400
