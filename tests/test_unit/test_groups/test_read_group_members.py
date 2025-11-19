import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_member_of_group_can_read_group_members(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)
    response = await client.get(
        f"v1/groups/{group.id}/users",
        headers={
            "Authorization": f"Bearer {user.token}",
        },
    )

    members = [
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
        for user in (
            group.get_member_of_role(UserTestRoles.Maintainer),
            group.get_member_of_role(UserTestRoles.Developer),
            group.get_member_of_role(UserTestRoles.Guest),
        )
    ]

    members.sort(key=lambda x: x["username"])
    assert response.status_code == 200, response.text
    assert response.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 3,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": members,
    }


async def test_groupless_user_cannot_read_group_members(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
):
    response = await client.get(
        f"v1/groups/{group.id}/users",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_other_group_member_cannot_read_group_members(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_guest_plus)
    response = await client.get(
        f"v1/groups/{group.id}/users",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_superuser_can_read_group_members(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
):
    response = await client.get(
        f"v1/groups/{group.id}/users",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    members = [
        {
            "id": user.id,
            "username": user.username,
            "role": user.role,
        }
        for user in (
            group.get_member_of_role(UserTestRoles.Maintainer),
            group.get_member_of_role(UserTestRoles.Developer),
            group.get_member_of_role(UserTestRoles.Guest),
        )
    ]
    members.sort(key=lambda x: x["username"])
    assert response.status_code == 200, response.text
    assert response.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 3,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": members,
    }


async def test_not_authorized_user_cannot_read_group_members(client: AsyncClient, group: MockGroup):
    response = await client.get(f"v1/groups/{group.id}/users")
    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_member_of_group_cannot_read_unknown_group_members_error(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)
    response = await client.get(
        "v1/groups/-1/users",
        headers={
            "Authorization": f"Bearer {user.token}",
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_read_unknown_group_members_error(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
):
    response = await client.get(
        "v1/groups/-1/users",
        headers={
            "Authorization": f"Bearer {superuser.token}",
        },
    )
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
