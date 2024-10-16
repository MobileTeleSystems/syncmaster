import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection
from tests.mocks import MockConnection, MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


async def test_maintainer_plus_can_delete_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_maintainer_plus: UserTestRoles,
    session: AsyncSession,
):
    # Arraange
    user = group_connection.owner_group.get_member_of_role(role_maintainer_plus)
    connection_id = group_connection.connection.id
    connection = await session.get(Connection, connection_id)
    assert not connection.is_deleted

    # Act
    result = await client.delete(
        f"v1/connections/{connection_id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was deleted",
    }
    assert result.status_code == 200
    deleted_connection = await session.get(Connection, connection_id)
    await session.refresh(deleted_connection)
    assert deleted_connection.is_deleted


# TODO: rename tests with simple_user to new group role name
async def test_groupless_user_cannot_delete_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    simple_user: MockUser,
    session: AsyncSession,
):
    # Act
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    # Assert
    assert result.status_code == 404
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    await session.refresh(group_connection.connection)
    assert not group_connection.connection.is_deleted


async def test_maintainer_plus_cannot_delete_connection_with_linked_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    role_maintainer_plus: UserTestRoles,
):
    # Arrange
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.delete(
        f"v1/connections/{group_transfer.source_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "The connection has an associated transfers. Number of the connected transfers: 1",
            "details": None,
        },
    }
    assert result.status_code == 409
    await session.refresh(group_transfer.source_connection)
    assert not group_transfer.source_connection.is_deleted


async def test_other_group_member_cannot_delete_group_connection(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = group.get_member_of_role(role_guest_plus)

    # Act
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.status_code == 404
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }


async def test_superuser_can_delete_group_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
):
    # Act
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was deleted",
    }


async def test_developer_or_below_cannot_delete_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_or_below: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_or_below)

    # Act
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    assert result.status_code == 403


async def test_unauthorized_user_cannot_delete_connection(client: AsyncClient, group_connection: MockConnection):
    # Act
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
    )

    # Assert
    assert result.status_code == 401
    assert result.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_maintainer_plus_delete_unknown_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
    role_maintainer_plus: UserTestRoles,
    session: AsyncSession,
):
    # Arraange
    user = group_connection.owner_group.get_member_of_role(role_maintainer_plus)

    # Act
    result = await client.delete(
        "v1/connections/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_superuser_delete_unknown_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
    superuser: MockUser,
):
    # Act
    result = await client.delete(
        "v1/connections/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    assert result.status_code == 404
