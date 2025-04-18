import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_owner_of_group_can_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    group_owner = group.get_member_of_role(UserTestRoles.Owner)
    result = await client.put(
        f"v1/groups/{group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    assert result.status_code == 200, result.json()
    assert result.json() == {"role": role_guest_plus_without_owner}


async def test_superuser_can_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    result = await client.put(
        f"v1/groups/{group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    assert result.status_code == 200, result.json()
    assert result.json() == {"role": role_guest_plus_without_owner}


async def test_owner_of_group_can_not_update_user_role_with_wrong_role(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    result = await client.put(
        f"v1/groups/{group.id}/users/{user.user.id}",
        headers={"Authorization": f"Bearer {group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "role": "Unknown",
        },
    )

    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "location": ["body"],
                    "message": "Value error, Input should be one of: Maintainer, Developer, Guest",
                    "code": "value_error",
                    "context": {},
                    "input": {"role": "Unknown"},
                },
            ],
        },
    }
    assert result.status_code == 422, result.json()


async def test_maintainer_below_can_not_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    updating_user = group.get_member_of_role(role_maintainer_or_below)
    user_to_update = group.get_member_of_role(role_guest_plus)
    result = await client.put(
        f"v1/groups/{group.id}/users/{user_to_update.user.id}",
        headers={"Authorization": f"Bearer {updating_user.token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    assert result.status_code == 403, result.json()


async def test_other_group_member_can_not_update_user_role(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_guest_plus)
    group_member = group.get_member_of_role(role_guest_plus_without_owner)
    result = await client.put(
        f"v1/groups/{group.id}/users/{group_member.user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": UserTestRoles.Maintainer,
        },
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404, result.json()


async def test_superuser_update_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    result = await client.put(
        f"v1/groups/-1/users/{user.user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_update_unknown_user_error(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
    role_guest_plus_without_owner: UserTestRoles,
):
    result = await client.put(
        f"v1/groups/{group.id}/users/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }


async def test_owner_of_group_update_unknown_user_error(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    group.get_member_of_role(role_maintainer_or_below)
    result = await client.put(
        f"v1/groups/{group.id}/users/-1",
        headers={"Authorization": f"Bearer {group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }


async def test_owner_of_group_update_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
    role_guest_plus_without_owner: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    result = await client.put(
        f"v1/groups/-1/users/{user.user.id}",
        headers={"Authorization": f"Bearer {group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "role": role_guest_plus_without_owner,
        },
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
