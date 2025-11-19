import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_guest_plus_can_read_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
    session: AsyncSession,
):
    user = group_connection.owner_group.get_member_of_role(role_guest_plus)

    response = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": group_connection.id,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "name": group_connection.name,
        "type": group_connection.type,
        "connection_data": {
            "database_name": group_connection.data["database_name"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "additional_params": group_connection.data["additional_params"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }


async def test_groupless_user_cannot_read_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    simple_user: MockUser,
):
    response = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {simple_user.token}"},
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_other_group_member_cannot_read_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)

    response = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_superuser_can_read_connection(
    client: AsyncClient,
    superuser: MockUser,
    group_connection: MockConnection,
):
    response = await client.get(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": group_connection.id,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "name": group_connection.name,
        "type": group_connection.type,
        "connection_data": {
            "database_name": group_connection.data["database_name"],
            "host": group_connection.data["host"],
            "port": group_connection.data["port"],
            "additional_params": group_connection.data["additional_params"],
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "user": group_connection.credentials.value["user"],
        },
    }


async def test_unauthorized_user_cannot_read_connection(client: AsyncClient, group_connection: MockConnection):
    response = await client.get(f"v1/connections/{group_connection.id}")

    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_guest_plus_cannot_read_unknown_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
    role_guest_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_guest_plus)

    response = await client.get(
        "v1/connections/-1",
        headers={"Authorization": f"Bearer {user.token}"},
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_superuser_cannot_read_unknown_connection_error(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
):
    response = await client.get(
        "v1/connections/-1",
        headers={"Authorization": f"Bearer {superuser.token}"},
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text
