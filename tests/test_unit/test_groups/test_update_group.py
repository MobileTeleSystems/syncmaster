import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_owner_of_group_can_update_group(
    client: AsyncClient,
    empty_group: MockGroup,
    session: AsyncSession,
):
    owner = empty_group.get_member_of_role(UserTestRoles.Owner)
    group_data = {
        "owner_id": empty_group.owner_id,
        "name": "New group name",
        "description": "some description",
    }
    response = await client.put(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {owner.token}"},
        json=group_data,
    )
    group_data.update({"id": empty_group.id})
    assert response.status_code == 200, response.text
    assert response.json() == group_data

    await session.refresh(empty_group.group)
    assert empty_group.group.name == group_data["name"]
    assert empty_group.group.description == group_data["description"]
    assert empty_group.group.owner_id == group_data["owner_id"]


async def test_groupless_user_cannot_update_group(client: AsyncClient, empty_group: MockGroup, simple_user: MockUser):
    group_data = {
        "owner_id": simple_user.id,
        "name": "New group name",
        "description": " asdf",
    }

    response = await client.put(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json=group_data,
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_other_group_member_cannot_update_group(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)
    group_data = {
        "owner_id": user.id,
        "name": "New group name",
        "description": " asdf",
    }

    response = await client.put(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json=group_data,
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_can_update_group(
    client: AsyncClient,
    empty_group: MockGroup,
    superuser: MockUser,
    session: AsyncSession,
):
    group_data = {
        "owner_id": empty_group.owner_id,
        "name": "New group name",
        "description": "some description",
    }

    response = await client.put(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )
    group_data.update({"id": empty_group.id})
    assert response.status_code == 200, response.text
    assert response.json() == group_data

    await session.refresh(empty_group.group)
    assert empty_group.group.name == group_data["name"]
    assert empty_group.group.description == group_data["description"]
    assert empty_group.group.owner_id == group_data["owner_id"]


@pytest.mark.parametrize(
    ("name", "error"),
    [
        pytest.param(
            "aa",
            {
                "context": {"min_length": 3},
                "input": "aa",
                "location": ["body", "name"],
                "message": "String should have at least 3 characters",
                "code": "string_too_short",
            },
            id="name_too_short",
        ),
        pytest.param(
            "a" * 129,
            {
                "context": {"max_length": 128},
                "input": "a" * 129,
                "location": ["body", "name"],
                "message": "String should have at most 128 characters",
                "code": "string_too_long",
            },
            id="name_too_long",
        ),
    ],
)
async def test_check_name_field_validation_on_update_group(
    client: AsyncClient,
    empty_group: MockGroup,
    name: str,
    error: dict,
):
    owner = empty_group.get_member_of_role(UserTestRoles.Owner)
    group_data = {
        "owner_id": empty_group.owner_id,
        "name": name,
        "description": name,
    }

    response = await client.put(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {owner.token}"},
        json=group_data,
    )

    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [error],
        },
    }


async def test_group_name_already_taken_error(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    superuser: MockUser,
):
    group_data = {
        "owner_id": empty_group.owner_id,
        "name": group.name,
        "description": "some description",
    }

    response = await client.put(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )
    assert response.status_code == 409, response.text
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "Group name already taken",
            "details": None,
        },
    }


async def test_owner_change_group_owner(client: AsyncClient, empty_group: MockGroup, simple_user: MockUser):
    previous_owner = empty_group.get_member_of_role(UserTestRoles.Owner)
    new_owner = simple_user

    # Change a group owner
    response = await client.put(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {previous_owner.token}"},
        json={
            "name": empty_group.name,
            "owner_id": new_owner.id,
            "description": empty_group.description,
        },
    )
    group_users_response = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {previous_owner.token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": empty_group.id,
        "name": empty_group.name,
        "owner_id": new_owner.id,
        "description": empty_group.description,
    }
    # Make sure previous owner became a guest in group
    assert group_users_response.status_code == 200, group_users_response.json()
    assert group_users_response.json()["items"] == [
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
    previous_owner = empty_group.get_member_of_role(UserTestRoles.Owner)
    new_owner = simple_user

    # Make user a group member
    await client.post(
        f"v1/groups/{empty_group.id}/users/{new_owner.id}",
        headers={"Authorization": f"Bearer {previous_owner.token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )
    # Upgrade user to a group owner
    response = await client.put(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {previous_owner.token}"},
        json={
            "name": empty_group.name,
            "owner_id": new_owner.id,
            "description": empty_group.description,
        },
    )
    group_users_response = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {new_owner.token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": empty_group.id,
        "name": empty_group.name,
        "owner_id": new_owner.id,
        "description": empty_group.description,
    }
    # Make sure previous owner became a guest in group
    # As well as upgraded owner is no longer considered a group member
    assert group_users_response.status_code == 200, group_users_response.json()
    assert group_users_response.json()["items"] == [
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
    response = await client.put(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": group.name,
            "owner_id": simple_user.id,
            "description": group.description,
        },
    )
    assert response.status_code == 403, response.text
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


async def test_not_authorized_user_cannot_update_group(client: AsyncClient, empty_group: MockGroup):
    response = await client.put(f"v1/groups/{empty_group.id}")
    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_owner_of_group_update_unknown_group_error(client: AsyncClient, empty_group: MockGroup):
    owner = empty_group.get_member_of_role(UserTestRoles.Owner)
    group_data = {
        "owner_id": empty_group.owner_id,
        "name": "New group name",
        "description": "some description",
    }
    response = await client.put(
        "v1/groups/-1",
        headers={"Authorization": f"Bearer {owner.token}"},
        json=group_data,
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_owner_of_group_update_group_unknown_owner_error(client: AsyncClient, empty_group: MockGroup):
    owner = empty_group.get_member_of_role(UserTestRoles.Owner)
    group_data = {
        "owner_id": -1,
        "name": "New group name",
        "description": "some description",
    }
    response = await client.put(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {owner.token}"},
        json=group_data,
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }


async def test_superuser_update_unknown_group_error(client: AsyncClient, empty_group: MockGroup, superuser: MockUser):
    group_data = {
        "owner_id": empty_group.owner_id,
        "name": "New group name",
        "description": "some description",
    }
    response = await client.put(
        "v1/groups/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
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
        "name": "New group name",
        "description": "some description",
    }
    response = await client.put(
        f"v1/groups/{empty_group.group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json=group_data,
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }
