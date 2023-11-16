import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, MockGroup, MockTransfer, MockUser, TestUserRoles

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_delete_connection(client: AsyncClient, group_connection: MockConnection):
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
    )
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


# TODO: rename tests with simple_user to new group role name
async def test_groupless_user_cannot_delete_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    simple_user: MockUser,
    session: AsyncSession,
):
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }
    await session.refresh(group_connection.connection)
    assert not group_connection.connection.is_deleted


async def test_group_maintainer_can_not_delete_connection_with_linked_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
):
    result = await client.delete(
        f"v1/connections/{group_transfer.source_connection.id}",
        headers={
            "Authorization": f"Bearer {group_transfer.owner_group.get_member_of_role(TestUserRoles.Maintainer).token}"
        },
    )
    assert result.json() == {
        "ok": False,
        "status_code": 409,
        "message": "The connection has an associated transfers. Number of the connected transfers: 1",
    }
    assert result.status_code == 409
    await session.refresh(group_transfer.source_connection)
    assert not group_transfer.source_connection.is_deleted


@pytest.mark.parametrize("user_role", [TestUserRoles.Owner, TestUserRoles.Maintainer])
async def test_delete_own_group_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    user_role: TestUserRoles,
):
    admin = group_connection.owner_group.get_member_of_role(user_role)
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {admin.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was deleted",
    }


async def test_group_owner_cannot_delete_other_group_connection(
    client: AsyncClient,
    empty_group: MockGroup,
    group_connection: MockConnection,
):
    other_admin = empty_group.get_member_of_role(TestUserRoles.Owner)
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {other_admin.token}"},
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


async def test_superuser_can_delete_group_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
):
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was deleted",
    }


async def test_not_owner_group_member_can_not_delete_connection(
    client: AsyncClient,
    group_connection: MockConnection,
):
    # Arrange
    group_member = group_connection.owner_group.get_member_of_role(TestUserRoles.User)

    # Act
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {group_member.token}"},
    )

    # Assert
    assert result.json() == {
        "message": "You have no power here",
        "ok": False,
        "status_code": 403,
    }
    assert result.status_code == 403
