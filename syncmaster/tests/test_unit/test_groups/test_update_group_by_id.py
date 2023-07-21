import pytest
from httpx import AsyncClient

from tests.utils import MockGroup, MockUser


@pytest.mark.asyncio
async def test_not_authorized_user_cannot_update_group(
    client: AsyncClient, empty_group: MockGroup
):
    result = await client.post(f"v1/groups/{empty_group.id}")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


@pytest.mark.asyncio
async def test_not_member_of_group_cannot_update_group(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    result = await client.post(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert (
        result.status_code == 422
    )  # TODO override standard validation handler Pydantic
    assert result.json() == {
        "detail": [
            {"loc": ["body"], "msg": "field required", "type": "value_error.missing"}
        ]
    }

    group_data = {
        "admin_id": simple_user.id,
        "name": "new_group_name",
        "description": " asdf",
    }
    result = await client.post(
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


@pytest.mark.asyncio
async def test_member_of_group_cannot_update_group(
    client: AsyncClient, not_empty_group: MockGroup
):
    user = not_empty_group.members[0]
    group_data = {"admin_id": user.id, "name": "new_group_name", "description": " asdf"}
    result = await client.post(
        f"v1/groups/{not_empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Group not found",
    }


@pytest.mark.asyncio
async def test_admin_of_group_can_update_group(
    client: AsyncClient, empty_group: MockGroup
):
    group_data = {
        "admin_id": empty_group.admin.id,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.post(
        f"v1/groups/{empty_group.id}",
        json=group_data,
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )
    assert result.status_code == 200
    group_data.update({"id": empty_group.id})
    assert result.json() == group_data

    # check update
    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == group_data


@pytest.mark.asyncio
async def test_superuser_can_update_group(
    client: AsyncClient, empty_group: MockGroup, superuser: MockUser
):
    group_data = {
        "admin_id": empty_group.admin.id,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.post(
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


@pytest.mark.asyncio
async def test_validation_on_update_group(
    client: AsyncClient,
    empty_group: MockGroup,
    not_empty_group: MockGroup,
    superuser: MockUser,
):
    result = await client.post(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 422
    assert result.json() == {
        "detail": [
            {"loc": ["body"], "msg": "field required", "type": "value_error.missing"}
        ]
    }

    group_data = {
        "admin_id": -1,
        "name": "new_group_name",
        "description": "some description",
    }
    result = await client.post(
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
        "name": not_empty_group.name,
        "description": "some description",
    }
    result = await client.post(
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


@pytest.mark.asyncio
async def test_change_group_admin(
    client: AsyncClient, empty_group: MockGroup, simple_user: MockUser
):
    result = await client.get(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "id": empty_group.id,
        "name": empty_group.name,
        "admin_id": empty_group.admin_id,
        "description": empty_group.description,
    }

    result = await client.post(
        f"v1/groups/{empty_group.id}",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
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
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
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
