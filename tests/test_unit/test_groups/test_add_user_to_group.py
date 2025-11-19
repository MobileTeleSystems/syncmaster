import pytest
from httpx import AsyncClient

from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_owner_can_add_user_to_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    user = empty_group.get_member_of_role(UserTestRoles.Owner)

    response = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )

    assert response.status_code == 204, response.text

    check_response = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert check_response.json() == {
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
                "role": role_maintainer_or_below,
            },
        ],
    }


async def test_groupless_user_cannot_add_user_to_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    response = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_maintainer_or_below_cannot_add_user_to_group(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    user = group.get_member_of_role(role_maintainer_or_below)

    response = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": role_maintainer_or_below,
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


async def test_owner_cannot_add_user_to_group_with_wrong_role(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
):
    user = group.get_member_of_role(UserTestRoles.Owner)

    response = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": "WrongRole",
        },
    )
    assert response.status_code == 422, response.text
    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "location": ["body"],
                    "message": "Value error, Input should be one of: Maintainer, Developer, Guest",
                    "code": "value_error",
                    "context": {},
                    "input": {"role": "WrongRole"},
                },
            ],
        },
    }


async def test_owner_cannot_add_user_to_group_without_role(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
):
    user = group.get_member_of_role(UserTestRoles.Owner)

    response = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 422, response.text
    assert response.json() == {
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


async def test_superuser_can_add_user_to_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
    superuser: MockUser,
):
    response = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )

    assert response.status_code == 204, response.text

    response = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 200, response.text
    assert response.json() == {
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
            },
        ],
    }


async def test_owner_cannot_add_user_to_group_twice(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
):
    user = group.get_member_of_role(UserTestRoles.Owner)

    response = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )
    assert response.status_code == 204, response.text

    response = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )
    assert response.status_code == 409, response.text
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "User already is group member",
            "details": None,
        },
    }


async def test_not_authorized_user_cannot_add_user_to_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    response = await client.post(f"v1/groups/{empty_group.id}/users/{simple_user.id}")

    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_owner_add_user_to_unknown_group_error(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    response = await client.post(
        f"v1/groups/-1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_owner_add_unknown_user_to_group_error(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    response = await client.post(
        f"v1/groups/{empty_group.id}/users/-1",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }


async def test_add_existing_owner_as_a_group_member(
    client: AsyncClient,
    empty_group: MockGroup,
    role_maintainer_or_below: UserTestRoles,
):
    user = empty_group.get_member_of_role(UserTestRoles.Owner)

    response = await client.post(
        f"v1/groups/{empty_group.id}/users/{empty_group.owner_id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )

    assert response.status_code == 409, response.text
    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "User already is group owner",
            "details": None,
        },
    }


async def test_superuser_add_user_to_unknown_group_error(
    client: AsyncClient,
    superuser: MockUser,
    simple_user: MockUser,
):
    response = await client.post(
        f"v1/groups/-1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_add_unknown_user_error(
    client: AsyncClient,
    superuser: MockUser,
    simple_user: MockUser,
    empty_group: MockGroup,
):
    response = await client.post(
        f"v1/groups/{empty_group.group.id}/users/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }
