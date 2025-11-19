import pytest
from httpx import AsyncClient

from tests.mocks import MockGroup, MockTransfer, MockUser, UserTestRoles
from tests.test_unit.utils import build_transfer_json

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_guest_plus_can_read_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_guest_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)

    response = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == build_transfer_json(group_transfer)


async def test_groupless_user_cannot_read_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    simple_user: MockUser,
):
    response = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_group_member_cannot_read_transfer_of_other_group(
    client: AsyncClient,
    group_transfer: MockTransfer,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)

    response = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_superuser_can_read_transfer(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    response = await client.get(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == build_transfer_json(group_transfer)


async def test_unauthorized_user_cannot_read_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    response = await client.get(f"v1/transfers/{group_transfer.id}")

    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_superuser_read_not_exist_transfer_error(
    client: AsyncClient,
    superuser: MockUser,
    group_transfer: MockTransfer,
):
    response = await client.get(
        "v1/transfers/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }


async def test_group_member_cannot_read_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_guest_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_guest_plus)

    response = await client.get(
        "v1/transfers/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Transfer not found",
            "details": None,
        },
    }
