import pytest
from httpx import AsyncClient
from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockGroup, MockUser, TestUserRoles

from app.db.models import UserGroup

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_read_groups(
    client: AsyncClient,
):
    result = await client.get("v1/groups")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_regular_user_cannot_get_any_groups(
    client: AsyncClient,
    simple_user: MockUser,
):
    # check get when simple user is not admin and not member of some group
    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 0,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [],
    }


async def test_regular_user_can_get_groups_if_member(
    client: AsyncClient,
    session: AsyncSession,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    session.add(
        UserGroup(
            group_id=empty_group.id,
            user_id=simple_user.id,
            role=simple_user.role,
        )
    )
    await session.commit()
    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 1,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": empty_group.id,
                "name": empty_group.name,
                "description": empty_group.description,
                "admin_id": empty_group.admin_id,
            }
        ],
    }


async def test_empty_groups_list_after_remove_from_group(
    client: AsyncClient,
    session: AsyncSession,
    group: MockGroup,
    simple_user: MockUser,
):
    user = group.get_member_of_role(TestUserRoles.User)
    result = await client.get("v1/groups", headers={"Authorization": f"Bearer {user.token}"})
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 1,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "admin_id": group.admin_id,
            }
        ],
    }

    await session.execute(delete(UserGroup).where(UserGroup.user_id == user.id, UserGroup.group_id == group.id))
    await session.commit()
    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 0,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [],
    }


async def test_superuser_can_read_all_groups(
    client: AsyncClient,
    superuser: MockUser,
    empty_group: MockGroup,
    group: MockGroup,
):
    result = await client.get(
        "v1/groups",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 2,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": empty_group.id,
                "name": empty_group.name,
                "description": empty_group.description,
                "admin_id": empty_group.admin_id,
            },
            {
                "id": group.id,
                "name": group.name,
                "description": group.description,
                "admin_id": group.admin_id,
            },
        ],
    }
