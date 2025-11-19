import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_owner_can_delete_anyone_from_group(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    group_owner = group.get_member_of_role(UserTestRoles.Owner)
    response = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {group_owner.token}"},
    )
    assert response.status_code == 204, response.text


async def test_groupless_user_cannot_remove_user_from_group(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    response = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_other_group_member_cannot_remove_user_from_group(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    other_group_member = group_connection.owner_group.get_member_of_role(role_guest_plus)
    response = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {other_group_member.token}"},
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_maintainer_and_user_can_delete_self_from_group(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below_without_guest: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below_without_guest)
    response = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 204, response.text


async def test_owner_cannot_delete_self_from_group(
    client: AsyncClient,
    group: MockGroup,
):
    user = group.get_member_of_role(UserTestRoles.Owner)
    response = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 409, response.text
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "User already is not group member",
            "details": None,
        },
    }


async def test_maintainer_or_below_cannot_delete_others_from_group(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus: UserTestRoles,
):
    if role_maintainer_or_below == role_guest_plus:
        pytest.skip()

    user = group.get_member_of_role(role_maintainer_or_below)
    other_group_member = group.get_member_of_role(role_guest_plus)
    response = await client.delete(
        f"v1/groups/{group.id}/users/{other_group_member.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert response.status_code == 403, response.text
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_superuser_can_delete_user_from_group(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    response = await client.delete(
        f"v1/groups/{group.id}/users/{user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 204, response.text


async def test_not_authorized_user_cannot_remove_user_from_group(client: AsyncClient, group: MockGroup):
    user = group.get_member_of_role(UserTestRoles.Developer)
    response = await client.delete(f"v1/groups/{group.id}/users/{user.id}")
    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_owner_delete_unknown_user_error(
    client: AsyncClient,
    group: MockGroup,
):
    group_owner = group.get_member_of_role(UserTestRoles.Owner)
    response = await client.delete(
        f"v1/groups/{group.id}/users/-1",
        headers={"Authorization": f"Bearer {group_owner.token}"},
    )
    assert response.status_code == 409, response.text
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "User already is not group member",
            "details": None,
        },
    }


async def test_owner_delete_user_from_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
):
    group_owner = group.get_member_of_role(UserTestRoles.Owner)
    user = group.get_member_of_role(role_maintainer_or_below)
    response = await client.delete(
        f"v1/groups/-1/users/{user.user.id}",
        headers={"Authorization": f"Bearer {group_owner.token}"},
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_delete_unknown_user_error(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
):
    response = await client.delete(
        f"v1/groups/{group.id}/users/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 409, response.text
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "User already is not group member",
            "details": None,
        },
    }


async def test_superuser_delete_user_from_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    response = await client.delete(
        f"v1/groups/-1/users/{user.user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
