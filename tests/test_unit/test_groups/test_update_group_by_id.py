import pytest
from httpx import AsyncClient

from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_owner_of_group_can_update_group(client: AsyncClient, empty_group: MockGroup):
    group_data = {
        "owner_id": empty_group.get_member_of_role(UserTestRoles.Owner).id,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
    )
    group_data.update({"id": empty_group.id})
    assert result.status_code == 200, result.json()
    assert result.json() == group_data

    check_result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
    )
    assert check_result.json() == {
        "data": group_data,
        "role": UserTestRoles.Owner,
    }
    assert check_result.status_code == 200


async def test_groupless_user_cannot_update_group(client: AsyncClient, empty_group: MockGroup, simple_user: MockUser):
    group_data = {
        "owner_id": simple_user.id,
        "name": "new_group_name",
        "description": " asdf",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404, result.json()


async def test_other_group_member_cannot_update_group(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)
    group_data = {
        "owner_id": user.id,
        "name": "new_group_name",
        "description": " asdf",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404, result.json()


async def test_superuser_can_update_group(client: AsyncClient, empty_group: MockGroup, superuser: MockUser):
    group_data = {
        "owner_id": empty_group.get_member_of_role(UserTestRoles.Owner).id,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    group_data.update({"id": empty_group.id})
    assert result.status_code == 200, result.json()
    assert result.json() == group_data

    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200, result.json()
    assert result.json() == {
        "data": group_data,
        "role": UserTestRoles.Superuser,
    }


async def test_validation_on_update_group(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    superuser: MockUser,
):
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 422, result.json()
    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "context": {},
                    "input": None,
                    "location": ["body"],
                    "message": "Field required",
                    "code": "missing",
                },
            ],
        },
    }

    group_data = {
        "owner_id": -1,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Admin not found",
            "details": None,
        },
    }
    group_data = {
        "owner_id": empty_group.owner_id,
        "name": group.name,
        "description": "some description",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 409, result.json()
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "Group name already taken",
            "details": None,
        },
    }


async def test_owner_change_group_owner(client: AsyncClient, empty_group: MockGroup, simple_user: MockUser):
    previous_owner = empty_group.owner
    new_owner = simple_user
    user = empty_group.get_member_of_role(UserTestRoles.Owner)

    # Change a group owner
    patch_result = await client.patch(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": empty_group.name,
            "owner_id": new_owner.id,
            "description": empty_group.description,
        },
    )
    group_users_result = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert patch_result.status_code == 200, patch_result.json()
    assert patch_result.json() == {
        "id": empty_group.id,
        "name": empty_group.name,
        "owner_id": new_owner.id,
        "description": empty_group.description,
    }
    # Make sure previous owner became a guest in group
    assert group_users_result.status_code == 200, patch_result.json()
    assert group_users_result.json()["items"] == [
        {
            "id": previous_owner.id,
            "username": previous_owner.username,
            "role": UserTestRoles.Guest,
        },
    ]


async def test_owner_change_group_owner_with_existing_role(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    previous_owner = empty_group.owner
    new_owner = simple_user
    user = empty_group.get_member_of_role(UserTestRoles.Owner)

    # Make user a group member
    await client.post(
        f"v1/groups/{empty_group.id}/users/{new_owner.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )
    # Upgrade user to a group owner
    patch_result = await client.patch(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": empty_group.name,
            "owner_id": new_owner.id,
            "description": empty_group.description,
        },
    )
    group_users_result = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert patch_result.status_code == 200, patch_result.json()
    assert patch_result.json() == {
        "id": empty_group.id,
        "name": empty_group.name,
        "owner_id": new_owner.id,
        "description": empty_group.description,
    }
    # Make sure previous owner became a guest in group
    # As well as upgraded owner is no longer considered a group member
    assert group_users_result.status_code == 200, group_users_result.json()
    assert group_users_result.json()["items"] == [
        {
            "id": previous_owner.id,
            "username": previous_owner.username,
            "role": UserTestRoles.Guest,
        },
    ]


async def test_maintainer_or_below_cannot_change_group_owner(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)
    result = await client.patch(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": group.name,
            "owner_id": simple_user.id,
            "description": group.description,
        },
    )
    assert result.status_code == 403, result.json()
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_not_authorized_user_cannot_update_group(client: AsyncClient, empty_group: MockGroup):
    result = await client.patch(f"v1/groups/{empty_group.id}")
    assert result.status_code == 401, result.json()
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_owner_of_group_update_unknown_group_error(client: AsyncClient, empty_group: MockGroup):
    group_data = {
        "owner_id": empty_group.get_member_of_role(UserTestRoles.Owner).id,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.patch(
        "v1/groups/-1",
        json=group_data,
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_owner_of_group_update_group_unknown_owner_error(client: AsyncClient, empty_group: MockGroup):
    group_data = {
        "owner_id": -1,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Admin not found",
            "details": None,
        },
    }


async def test_superuser_update_unknown_group_error(client: AsyncClient, empty_group: MockGroup, superuser: MockUser):
    group_data = {
        "owner_id": empty_group.get_member_of_role(UserTestRoles.Owner).id,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.patch(
        "v1/groups/-1",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_update_group_unknown_owner_error(
    client: AsyncClient,
    empty_group: MockGroup,
    superuser: MockUser,
):
    group_data = {
        "owner_id": -1,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Admin not found",
            "details": None,
        },
    }
