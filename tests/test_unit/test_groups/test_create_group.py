import secrets

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from tests.mocks import MockUser

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_simple_user_can_create_group(
    simple_user: MockUser,
    session: AsyncSession,
    client: AsyncClient,
):
    group_name = f"{secrets.token_hex(5)}"
    group_data = {
        "name": group_name,
        "description": "description of new test group",
    }

    response = await client.post(
        "v1/groups",
        json=group_data,
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 200, response.text

    group = (await session.scalars(select(Group).where(Group.name == group_name))).one()
    assert (
        response.json()
        == {
            "id": group.id,
            "owner_id": simple_user.user.id,
        }
        | group_data
    )

    assert group.name == group_data["name"]
    assert group.description == group_data["description"]
    assert group.owner_id == simple_user.user.id


async def test_simple_user_cannot_create_group_twice(
    client: AsyncClient,
    simple_user: MockUser,
):
    group_data = {
        "name": "test_superuser_cannot_create_group_twice",
        "description": "description of new test group",
        "owner_id": simple_user.id,
    }

    response = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json=group_data,
    )
    assert response.status_code == 200, response.text

    second_response = await client.post(
        "v1/groups",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json=group_data,
    )
    assert second_response.status_code == 409
    assert second_response.json() == {
        "error": {
            "code": "conflict",
            "message": "Group name already taken",
            "details": None,
        },
    }


async def test_not_authorized_user_cannot_create_group(
    client: AsyncClient,
    simple_user: MockUser,
):
    group_data = {
        "name": "new_test_group",
        "description": "description of new test group",
        "owner_id": simple_user.id,
    }

    response = await client.post("v1/groups", json=group_data)

    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }
