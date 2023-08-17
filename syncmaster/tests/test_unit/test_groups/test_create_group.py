import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Group
from tests.utils import MockUser

pytestmark = [pytest.mark.asyncio]


async def test_not_authorized_user_cannot_create_group(
    client: AsyncClient,
    simple_user: MockUser,
):
    group_data = {
        "name": "new_test_group",
        "description": "description of new test group",
        "admin_id": simple_user.id,
    }

    result = await client.post("v1/groups", json=group_data)
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_regular_user_cannot_create_group(
    client: AsyncClient,
    simple_user: MockUser,
):
    # check simple user cannot create group
    group_data = {
        "name": "new_test_group",
        "description": "description of new test group",
        "admin_id": simple_user.id,
    }
    result = await client.post(
        "v1/groups",
        json=group_data,
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_superuser_can_create_group(
    client: AsyncClient,
    session: AsyncSession,
    simple_user: MockUser,
    superuser: MockUser,
):
    # check superuser can create group
    group_data = {
        "name": "new_test_group",
        "description": "description of new test group",
        "admin_id": simple_user.id,
    }
    result = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )
    assert result.status_code == 200
    group = (
        await session.scalars(select(Group).where(Group.name == group_data["name"]))
    ).one()
    assert result.json() == {
        "id": group.id,
        "name": group_data["name"],
        "admin_id": group_data["admin_id"],
        "description": group_data["description"],
    }


async def test_superuser_cannot_create_group_twice(
    client: AsyncClient,
    simple_user: MockUser,
    superuser: MockUser,
):
    # check superuser cannot create group twice
    group_data = {
        "name": "test_superuser_cannot_create_group_twice",
        "description": "description of new test group",
        "admin_id": simple_user.id,
    }
    result = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )
    assert result.status_code == 200

    result = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Group name already taken",
    }


async def test_superuser_cannot_create_group_with_incorrect_admin_id(
    client: AsyncClient,
    superuser: MockUser,
):
    # check superuser cannot create group with incorrect admin id
    group_data = {
        "name": "new_another_group",
        "description": "description of new test group",
        "admin_id": -123,
    }
    result = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Admin not found",
    }
