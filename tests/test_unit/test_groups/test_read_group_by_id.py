import pytest
from httpx import AsyncClient

from tests.mocks import MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_member_of_group_can_read_by_id(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)
    result = await client.get(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.status_code == 200, result.json()
    assert result.json() == {
        "data": {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "owner_id": group.owner_id,
        },
        "role": user.role.value,
    }


async def test_groupless_user_cannot_read_group(
    client: AsyncClient,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    result = await client.get(
        f"v1/groups/{empty_group.id}",
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


async def test_other_member_group_cannot_read_group(
    client: AsyncClient,
    empty_group: MockGroup,
    group: MockGroup,
    simple_user: MockUser,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)
    result = await client.get(
        f"v1/groups/{empty_group.id}",
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


async def test_superuser_can_read_group(
    client: AsyncClient,
    group: MockGroup,
    superuser: MockUser,
):
    result = await client.get(
        f"v1/groups/{group.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200, result.json()
    assert result.json() == {
        "data": {
            "id": group.id,
            "name": group.name,
            "description": group.description,
            "owner_id": group.owner_id,
        },
        "role": superuser.role.value,
    }


async def test_not_authorized_user_cannot_read_by_id(
    client: AsyncClient,
    empty_group: MockGroup,
):
    result = await client.get(f"v1/groups/{empty_group.id}")
    assert result.status_code == 401, result.json()
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_member_of_group_read_unknown_group_error(
    client: AsyncClient,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)
    result = await client.get(
        "v1/groups/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )
    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }


async def test_superuser_read_unknown_group_error(
    client: AsyncClient,
    superuser: MockUser,
):
    result = await client.get(
        "v1/groups/-1",
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
