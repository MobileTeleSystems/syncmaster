import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_not_authorized_user_cannot_delete_group(client: AsyncClient, empty_group: MockGroup):
    result = await client.delete(f"v1/groups/{empty_group.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_not_member_of_group_cannot_delete_group(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    result = await client.delete(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_member_of_group_cannot_delete_group(client: AsyncClient, group: MockGroup):
    user = group.get_member_of_role(TestUserRoles.User)

    result = await client.delete(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_admin_of_group_cannot_delete_group(client: AsyncClient, empty_group: MockGroup):
    result = await client.delete(
        f"v1/groups/{empty_group.id}",
        headers={
            "Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}",
        },
    )
    assert result.status_code == 403
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }


async def test_superuser_can_delete_group(client: AsyncClient, empty_group: MockGroup, superuser: MockUser):
    result = await client.delete(
        f"v1/groups/{empty_group.id}",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Group was deleted",
    }

    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }

    result = await client.get(
        "v1/groups",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
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


async def test_cannot_delete_group_twice(client: AsyncClient, empty_group: MockGroup, superuser: MockUser):
    result = await client.delete(
        f"v1/groups/{empty_group.id}",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Group was deleted",
    }

    result = await client.delete(
        f"v1/groups/{empty_group.id}",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }
