import pytest
from httpx import AsyncClient

from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_owner_of_group_can_update_group(client: AsyncClient, empty_group: MockGroup):
    # Arrange
    group_data = {
        "owner_id": empty_group.get_member_of_role(UserTestRoles.Owner).id,
        "name": "new_group_name",
        "description": "some description",
    }
    # Act
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
    )
    # Assert
    group_data.update({"id": empty_group.id})
    assert result.json() == group_data
    assert result.status_code == 200

    check_result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
    )
    assert check_result.json() == group_data
    assert check_result.status_code == 200


async def test_groupless_user_cannot_update_group(client: AsyncClient, empty_group: MockGroup, simple_user: MockUser):
    # Arrange
    group_data = {
        "owner_id": simple_user.id,
        "name": "new_group_name",
        "description": " asdf",
    }
    # Act
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }
    assert result.status_code == 404


async def test_other_group_member_cannot_update_group(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)
    group_data = {
        "owner_id": user.id,
        "name": "new_group_name",
        "description": " asdf",
    }
    # Act
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {user.token}"},
    )
    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }
    assert result.status_code == 404


async def test_superuser_can_update_group(client: AsyncClient, empty_group: MockGroup, superuser: MockUser):
    # Arrange
    group_data = {
        "owner_id": empty_group.get_member_of_role(UserTestRoles.Owner).id,
        "name": "new_group_name",
        "description": "some description",
    }
    # Act
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    group_data.update({"id": empty_group.id})
    assert result.json() == group_data
    assert result.status_code == 200

    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == group_data


async def test_validation_on_update_group(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    superuser: MockUser,
):
    # Act
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {
                "input": None,
                "loc": ["body"],
                "msg": "Field required",
                "type": "missing",
                "url": "https://errors.pydantic.dev/2.6/v/missing",
            }
        ]
    }

    # Arrange
    group_data = {
        "owner_id": -1,
        "name": "new_group_name",
        "description": "some description",
    }
    # Act
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Admin not found",
    }
    # Arrange
    group_data = {
        "owner_id": empty_group.owner_id,
        "name": group.name,
        "description": "some description",
    }
    # Act
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Group name already taken",
    }


async def test_owner_change_group_owner(client: AsyncClient, empty_group: MockGroup, simple_user: MockUser):
    # Act
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
        json={
            "name": empty_group.name,
            "owner_id": simple_user.id,
            "description": empty_group.description,
        },
    )
    # Assert
    assert result.json() == {
        "id": empty_group.id,
        "name": empty_group.name,
        "owner_id": simple_user.id,
        "description": empty_group.description,
    }
    assert result.status_code == 200


async def test_maintainer_or_below_cannot_change_group_owner(
    client: AsyncClient,
    group: MockGroup,
    simple_user: MockUser,
    role_maintainer_or_below: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_maintainer_or_below)
    # Act
    result = await client.patch(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "name": group.name,
            "owner_id": simple_user.id,
            "description": group.description,
        },
    )
    # Assert
    assert result.json() == {
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }
    assert result.status_code == 403


async def test_not_authorized_user_cannot_update_group(client: AsyncClient, empty_group: MockGroup):
    # Act
    result = await client.patch(f"v1/groups/{empty_group.id}")
    # Assert
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }
    assert result.status_code == 401


async def test_owner_of_group_update_unknown_group_error(client: AsyncClient, empty_group: MockGroup):
    # Arrange
    group_data = {
        "owner_id": empty_group.get_member_of_role(UserTestRoles.Owner).id,
        "name": "new_group_name",
        "description": "some description",
    }
    # Act
    result = await client.patch(
        "v1/groups/-1",
        json=group_data,
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
    )
    # Assert
    group_data.update({"id": empty_group.id})
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }


async def test_owner_of_group_update_group_unknown_owner_error(client: AsyncClient, empty_group: MockGroup):
    # Arrange
    group_data = {
        "owner_id": -1,
        "name": "new_group_name",
        "description": "some description",
    }
    # Act
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(UserTestRoles.Owner).token}"},
    )
    # Assert
    group_data.update({"id": empty_group.id})
    assert result.json() == {
        "message": "Admin not found",
        "ok": False,
        "status_code": 400,
    }


async def test_superuser_update_unknown_group_error(client: AsyncClient, empty_group: MockGroup, superuser: MockUser):
    # Arrange
    group_data = {
        "owner_id": empty_group.get_member_of_role(UserTestRoles.Owner).id,
        "name": "new_group_name",
        "description": "some description",
    }
    # Act
    result = await client.patch(
        "v1/groups/-1",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    group_data.update({"id": empty_group.id})
    assert result.json() == {
        "message": "Group not found",
        "ok": False,
        "status_code": 404,
    }


async def test_superuser_update_group_unknown_owner_error(
    client: AsyncClient,
    empty_group: MockGroup,
    superuser: MockUser,
):
    # Arrange
    group_data = {
        "owner_id": -1,
        "name": "new_group_name",
        "description": "some description",
    }
    # Act
    result = await client.patch(
        f"v1/groups/{empty_group.group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    # Assert
    group_data.update({"id": empty_group.id})
    assert result.json() == {
        "message": "Admin not found",
        "ok": False,
        "status_code": 400,
    }
