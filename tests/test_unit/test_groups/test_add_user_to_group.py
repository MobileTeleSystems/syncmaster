import pytest
from httpx import AsyncClient

from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


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
    assert result.status_code == 200

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
            }
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
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }
    assert result.status_code == 404


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
        "ok": False,
        "status_code": 403,
        "message": "You have no power here",
    }
    assert result.status_code == 403


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
        "detail": [
            {
                "ctx": {"enum_values": ["Maintainer", "Developer", "Guest"]},
                "loc": ["body", "role"],
                "msg": "value is not a valid enumeration member; permitted: 'Maintainer', 'Developer', 'Guest'",
                "type": "type_error.enum",
            }
        ]
    }
    assert result.status_code == 422


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
        "detail": [
            {
                "loc": ["body"],
                "msg": "field required",
                "type": "value_error.missing",
            },
        ],
    }
    assert result.status_code == 422


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
    assert result.status_code == 200

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
    assert result.status_code == 200
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
        "ok": False,
        "status_code": 400,
        "message": "User already is group member",
    }
    assert result.status_code == 400


async def test_not_authorized_user_cannot_add_user_to_group(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    # Act
    result = await client.post(f"v1/groups/{empty_group.id}/users/{simple_user.id}")

    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
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
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }
    assert result.status_code == 404


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
        "message": "User not found",
        "ok": False,
        "status_code": 404,
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
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }
    assert result.status_code == 404


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
        "ok": False,
        "status_code": 404,
        "message": "User not found",
    }
    assert result.status_code == 404
