import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection
from tests.mocks import MockConnection, MockGroup, MockTransfer, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_maintainer_plus_can_delete_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_maintainer_plus: UserTestRoles,
    session: AsyncSession,
):
    user = group_connection.owner_group.get_member_of_role(role_maintainer_plus)
    connection_id = group_connection.connection.id
    connection = await session.get(Connection, connection_id)
    assert connection is not None

    result = await client.delete(
        f"v1/connections/{connection_id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert result.status_code == 200, result.json()
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was deleted",
    }
    session.expunge(connection)
    connection = await session.get(Connection, connection_id)
    assert connection is None


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

    assert result.status_code == 404, result.json()
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }

    session.expunge(group_connection)
    connection = await session.get(Connection, group_connection.id)
    assert connection is not None


async def test_maintainer_plus_cannot_delete_connection_with_linked_transfer(
    client: AsyncClient,
    group_transfer: MockTransfer,
    session: AsyncSession,
    role_maintainer_plus: UserTestRoles,
):
    user = group_transfer.owner_group.get_member_of_role(role_maintainer_plus)

    result = await client.delete(
        f"v1/connections/{group_transfer.source_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "The connection has an associated transfers. Number of the connected transfers: 1",
            "details": None,
        },
    }
    assert result.status_code == 409, result.json()
    session.expunge(group_transfer.source_connection)
    connection = await session.get(Connection, group_transfer.source_connection.id)
    assert connection is not None


async def test_other_group_member_cannot_delete_group_connection(
    client: AsyncClient,
    group: MockGroup,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)

    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert result.status_code == 404, result.json()
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
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert result.status_code == 200, result.json()
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
    user = group_connection.owner_group.get_member_of_role(role_developer_or_below)

    result = await client.delete(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert result.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    assert result.status_code == 403, result.json()


async def test_unauthorized_user_cannot_delete_connection(client: AsyncClient, group_connection: MockConnection):
    result = await client.delete(
        f"v1/connections/{group_connection.id}",
    )

    assert result.status_code == 401, result.json()
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

    result = await client.delete(
        "v1/connections/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    assert result.status_code == 404, result.json()


async def test_superuser_delete_unknown_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
    session: AsyncSession,
    superuser: MockUser,
):
    result = await client.delete(
        "v1/connections/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    assert result.status_code == 404, result.json()
