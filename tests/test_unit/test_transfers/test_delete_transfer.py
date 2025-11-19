import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Transfer
from tests.mocks import MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_maintainer_plus_can_delete_group_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_maintainer_plus: UserTestRoles,
    session: AsyncSession,
):
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)
    transfer = await session.get(Transfer, group_transfer.id)

    response = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 204, response.text
    session.expunge(transfer)
    transfer_in_db = await session.get(Transfer, transfer.id)
    assert transfer_in_db is None


async def test_superuser_can_delete_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    superuser: MockUser,
    session: AsyncSession,
):
    transfer = await session.get(Transfer, group_transfer.id)

    response = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert response.status_code == 204, response.text
    session.expunge(transfer)
    transfer_in_db = await session.get(Transfer, transfer.id)
    assert transfer_in_db is None


async def test_groupless_user_cannot_delete_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    simple_user: MockUser,
):
    response = await client.delete(
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


async def test_developer_or_below_cannot_delete_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    role_developer_or_below: UserTestRoles,
):
    transfer = await session.get(Transfer, group_transfer.id)
    user = group_transfer.owner_group.get_member_of_role(role_developer_or_below)

    response = await client.delete(
        f"v1/transfers/{group_transfer.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 403, response.text
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    session.expunge(transfer)
    transfer_in_db = await session.get(Transfer, transfer.id)
    assert transfer_in_db is not None


async def test_group_member_cannot_delete_other_group_transfer(
    client: AsyncClient,
    group: MockGroup,
    group_transfer: MockTransfer,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)

    response = await client.delete(
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


async def test_unauthorized_user_cannot_delete_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
):
    response = await client.delete(
        f"v1/transfers/{group_transfer.id}",
    )

    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_superuser_cannot_delete_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    superuser: MockUser,
):
    response = await client.delete(
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


async def test_maintainer_plus_cannot_delete_unknown_transfer_error(
    client: AsyncClient,
    group_transfer: MockTransfer,
    role_maintainer_plus: UserTestRoles,
    session: AsyncSession,
):
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    response = await client.delete(
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
