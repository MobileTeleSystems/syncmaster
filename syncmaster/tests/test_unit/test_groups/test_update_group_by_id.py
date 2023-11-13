import pytest
from httpx import AsyncClient
from tests.utils import MockGroup, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_not_authorized_user_cannot_update_group(client: AsyncClient, empty_group: MockGroup):
    result = await client.patch(f"v1/groups/{empty_group.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_not_member_of_group_cannot_update_group(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 422  # TODO override standard validation handler Pydantic
    assert result.json() == {"detail": [{"loc": ["body"], "msg": "field required", "type": "value_error.missing"}]}

    group_data = {
        "admin_id": simple_user.id,
        "name": "new_group_name",
        "description": " asdf",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


@pytest.mark.parametrize(
    "group_member_role",
    [
        TestUserRoles.Maintainer,
        TestUserRoles.User,
        TestUserRoles.Guest,
    ],
)
async def test_member_of_group_cannot_update_group(
    client: AsyncClient,
    group: MockGroup,
    group_member_role: str,
):
    user = group.get_member_of_role(group_member_role)
    group_data = {"admin_id": user.id, "name": "new_group_name", "description": " asdf"}
    result = await client.patch(
        f"v1/groups/{group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.json() == {
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }
    assert result.status_code == 403


async def test_admin_of_group_can_update_group(client: AsyncClient, empty_group: MockGroup):
    group_data = {
        "admin_id": empty_group.get_member_of_role("Owner").id,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
    )
    assert result.status_code == 200
    group_data.update({"id": empty_group.id})
    assert result.json() == group_data

    # check update
    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
    )
    assert result.status_code == 200
    assert result.json() == group_data


async def test_superuser_can_update_group(client: AsyncClient, empty_group: MockGroup, superuser: MockUser):
    group_data = {
        "admin_id": empty_group.get_member_of_role("Owner").id,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    group_data.update({"id": empty_group.id})
    assert result.json() == group_data

    # check update
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
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 422
    assert result.json() == {"detail": [{"loc": ["body"], "msg": "field required", "type": "value_error.missing"}]}

    group_data = {
        "admin_id": -1,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Admin not found",
    }

    group_data = {
        "admin_id": empty_group.admin_id,
        "name": group.name,
        "description": "some description",
    }
    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 400
    assert result.json() == {
        "ok": False,
        "status_code": 400,
        "message": "Group name already taken",
    }


async def test_change_group_admin(client: AsyncClient, empty_group: MockGroup, simple_user: MockUser):
    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": empty_group.id,
        "name": empty_group.name,
        "admin_id": empty_group.admin_id,
        "description": empty_group.description,
    }

    result = await client.patch(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
        json={
            "name": empty_group.name,
            "admin_id": simple_user.id,
            "description": empty_group.description,
        },
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": empty_group.id,
        "name": empty_group.name,
        "admin_id": simple_user.id,
        "description": empty_group.description,
    }

    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.get_member_of_role(TestUserRoles.Owner).token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }

    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": empty_group.id,
        "name": empty_group.name,
        "admin_id": simple_user.id,
        "description": empty_group.description,
    }
