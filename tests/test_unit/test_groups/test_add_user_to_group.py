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
    # Arrange
    user = empty_group.get_member_of_role(UserTestRoles.Owner)

    # Act
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )

    # Assert
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully added to group",
    }
    assert result.status_code == 200, result.json()
    check_result = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert check_result.json() == {
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
    # Act
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )
    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404, result.json()


async def test_maintainer_or_below_cannot_add_user_to_group(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)

    # Act
    result = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    assert result.status_code == 403, result.json()


async def test_owner_cannot_add_user_to_group_with_wrong_role(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
):
    # Arrange
    user = group.get_member_of_role(UserTestRoles.Owner)

    # Act
    result = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": "WrongRole",
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
                    "input": {"role": "WrongRole"},
                },
            ],
        },
    }
    assert result.status_code == 422, result.json()


async def test_owner_cannot_add_user_to_group_without_role(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
):
    # Arrange
    user = group.get_member_of_role(UserTestRoles.Owner)

    # Act
    result = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
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
    assert result.status_code == 422, result.json()


async def test_superuser_can_add_user_to_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
    superuser: MockUser,
):
    # Act
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )

    # Assert
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully added to group",
    }
    assert result.status_code == 200, result.json()
    result = await client.get(
        f"v1/groups/{empty_group.id}/users",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200, result.json()
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
            },
        ],
    }


async def test_owner_cannot_add_user_to_group_twice(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
):
    # Arrange
    user = group.get_member_of_role(UserTestRoles.Owner)

    # Act
    result = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )
    # Assert
    assert result.status_code == 200, result.json()
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "User was successfully added to group",
    }

    result = await client.post(
        f"v1/groups/{group.id}/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "User already is group member",
            "details": None,
        },
    }
    assert result.status_code == 409, result.json()


async def test_not_authorized_user_cannot_add_user_to_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    # Act
    result = await client.post(f"v1/groups/{empty_group.id}/users/{simple_user.id}")

    # Assert
    assert result.status_code == 401, result.json()
    assert result.json() == {
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
    # Act
    result = await client.post(
        f"v1/groups/-1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404, result.json()


async def test_owner_add_unknown_user_to_group_error(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    # Act
    result = await client.post(
        f"v1/groups/{empty_group.id}/users/-1",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )

    # Assert
    assert result.json() == {
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

    result = await client.post(
        f"v1/groups/{empty_group.id}/users/{empty_group.owner_id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "role": role_maintainer_or_below,
        },
    )

    assert result.status_code == 409, result.json()
    assert result.json() == {
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
    # Act
    result = await client.post(
        f"v1/groups/-1/users/{simple_user.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404, result.json()


async def test_superuser_add_unknown_user_error(
    client: AsyncClient,
    superuser: MockUser,
    simple_user: MockUser,
    empty_group: MockGroup,
):
    # Act
    result = await client.post(
        f"v1/groups/{empty_group.group.id}/users/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "role": UserTestRoles.Developer,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }
    assert result.status_code == 404, result.json()
