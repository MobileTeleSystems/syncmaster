import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_not_authorized_user_cannot_add_user_to_group(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    result = await client.post(f"v1/groups/{empty_group.id}/users/{simple_user.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_not_member_group_cannot_add_user_to_group(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "role": TestUserRoles.User,
        },
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


async def test_guest_cannot_add_user_to_group(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
):
    # Act
    user = group.get_member_of_role(TestUserRoles.Guest)
    result = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": TestUserRoles.Guest,
        },
    )

    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }
    assert result.status_code == 403


async def test_owner_of_group_can_add_user_to_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
        json={
            "role": TestUserRoles.User,
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully added to group",
    }

    result = await client.get(
        f"v1/groups/{empty_group.id}/users",
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
                "id": simple_user.id,
                "username": simple_user.username,
                "role": simple_user.role,
            }
        ],
    }


async def test_owner_of_group_can_not_add_user_to_group_with_wrong_role(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
        json={
            "role": "WrongRole",
        },
    )
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "ctx": {"enum_values": ["Maintainer", "User", "Guest"]},
                "loc": ["body", "role"],
                "msg": "value is not a valid enumeration member; permitted: 'Maintainer', 'User', 'Guest'",
                "type": "type_error.enum",
            }
        ]
    }


async def test_owner_of_group_can_not_add_user_to_group_without_role(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
    )
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "loc": ["body"],
                "msg": "field required",
                "type": "value_error.missing",
            },
        ],
    }


async def test_superuser_can_add_user_to_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
    superuser: MockUser,
):
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": TestUserRoles.User,
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully added to group",
    }

    result = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {superuser.token}"},
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
                "id": simple_user.id,
                "username": simple_user.username,
                "role": simple_user.role,
            }
        ],
    }


async def test_cannot_add_user_to_group_twice(client: AsyncClient, empty_group: MockGroup, simple_user: MockUser):
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
        json={
            "role": TestUserRoles.User,
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully added to group",
    }

    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
        json={
            "role": TestUserRoles.User,
        },
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "User already is group member",
    }


async def test_cannot_add_user_to_incorrect_group(
    client: AsyncClient,
    superuser: MockUser,
    simple_user: MockUser,
):
    result = await client.post(
        f"v1/groups/-1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": TestUserRoles.User,
        },
    )
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }
    assert result.status_code == 404
