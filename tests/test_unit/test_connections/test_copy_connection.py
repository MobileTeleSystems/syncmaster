import secrets

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import AuthData, Connection
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server]


async def test_developer_plus_can_copy_connection_without_remove_source(
    client: AsyncClient,
    session: AsyncSession,
    settings: Settings,
    group_connection_and_group_developer_plus: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    role = group_connection_and_group_developer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    old_connection = await session.get(Connection, group_connection.id)
    old_auth_data = await session.get(AuthData, group_connection.id)
    old_credentials = decrypt_auth_data(old_auth_data.value, settings)

    new_connection_query = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    new_connection = (await session.scalars(new_connection_query)).one_or_none()
    assert not new_connection

    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
            "remove_source": False,
        },
    )

    assert response.status_code == 200, response.text

    # new connection with new name exist in target group
    new_connection = (await session.scalars(new_connection_query)).one()

    assert response.json() == {
        "id": new_connection.id,
        "group_id": empty_group.group.id,
        "name": old_connection.name,
        "description": old_connection.description,
        "type": old_connection.type,
        "connection_data": {
            "host": old_connection.data["host"],
            "port": old_connection.data["port"],
            "database_name": old_connection.data["database_name"],
            "additional_params": old_connection.data["additional_params"],
        },
        "auth_data": None,
    }

    new_auth_data = await session.get(AuthData, new_connection.id)
    assert new_auth_data is None

    # Check old (original) connection still exists
    session.expunge(old_connection)
    old_connection = await session.get(Connection, group_connection.id)
    assert old_connection is not None

    # Check old auth_data is unchanged
    session.expunge(old_auth_data)
    old_auth_data = await session.get(AuthData, group_connection.id)
    assert decrypt_auth_data(old_auth_data.value, settings) == old_credentials


async def test_developer_plus_can_copy_connection_with_new_connection_name(
    client: AsyncClient,
    session: AsyncSession,
    settings: Settings,
    group_connection_and_group_developer_plus: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    role = group_connection_and_group_developer_plus
    user = group_connection.owner_group.get_member_of_role(role)
    new_name = f"{secrets.token_hex(5)}"

    old_connection = await session.get(Connection, group_connection.id)
    old_auth_data = await session.get(AuthData, group_connection.id)
    old_credentials = decrypt_auth_data(old_auth_data.value, settings)

    new_connection_query = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == new_name,
    )
    new_connection = (await session.scalars(new_connection_query)).one_or_none()
    assert not new_connection

    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
            "new_name": new_name,
        },
    )

    assert response.status_code == 200, response.text

    # new connection with new name exist in target group
    new_connection = (await session.scalars(new_connection_query)).one()

    assert response.json() == {
        "id": new_connection.id,
        "group_id": empty_group.group.id,
        "name": new_name,
        "description": old_connection.description,
        "type": old_connection.type,
        "connection_data": {
            "host": old_connection.data["host"],
            "port": old_connection.data["port"],
            "database_name": old_connection.data["database_name"],
            "additional_params": old_connection.data["additional_params"],
        },
        "auth_data": None,
    }

    new_auth_data = await session.get(AuthData, new_connection.id)
    assert new_auth_data is None

    # Check old (original) connection still exists
    session.expunge(old_connection)
    old_connection = await session.get(Connection, group_connection.id)
    assert old_connection is not None

    # Check old auth_data is unchanged
    session.expunge(old_auth_data)
    old_auth_data = await session.get(AuthData, group_connection.id)
    assert decrypt_auth_data(old_auth_data.value, settings) == old_credentials


async def test_developer_below_can_not_copy_connection_with_remove_source(
    client: AsyncClient,
    group_connection_and_group_developer_or_below: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    role = group_connection_and_group_developer_or_below
    user = group_connection.owner_group.get_member_of_role(role)

    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
            "remove_source": True,
        },
    )

    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
    assert response.status_code == 403, response.text


async def test_maintainer_plus_can_copy_connection_and_delete_source(
    client: AsyncClient,
    session: AsyncSession,
    group_connection: MockConnection,
    empty_group: MockGroup,
    group_connection_and_group_maintainer_plus: str,
):
    role = group_connection_and_group_maintainer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    old_connection = await session.get(Connection, group_connection.id)
    old_auth_data = await session.get(AuthData, group_connection.id)

    new_connection_query = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    new_connection = (await session.scalars(new_connection_query)).one_or_none()
    assert not new_connection

    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
            "remove_source": True,
        },
    )

    assert response.status_code == 200, response.text

    # new connection with new name exist in target group
    new_connection = (await session.scalars(new_connection_query)).one()

    assert response.json() == {
        "id": new_connection.id,
        "group_id": empty_group.group.id,
        "name": old_connection.name,
        "description": old_connection.description,
        "type": old_connection.type,
        "connection_data": {
            "host": old_connection.data["host"],
            "port": old_connection.data["port"],
            "database_name": old_connection.data["database_name"],
            "additional_params": old_connection.data["additional_params"],
        },
        "auth_data": None,
    }

    new_auth_data = await session.get(AuthData, new_connection.id)
    assert new_auth_data is None

    # Check old (original) connection was removed
    session.expunge(old_connection)
    old_connection = await session.get(Connection, group_connection.id)
    assert old_connection is None

    # Check old auth_data is removed too
    session.expunge(old_auth_data)
    old_auth_data = await session.get(AuthData, group_connection.id)
    assert old_auth_data is None


async def test_maintainer_plus_cannot_copy_connection_with_same_name_in_new_group(
    client: AsyncClient,
    group_connection_with_same_name_maintainer_plus: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    role = group_connection_with_same_name_maintainer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )

    assert response.json() == {
        "error": {
            "code": "conflict",
            "message": "The connection name already exists in the target group, please specify a new one",
            "details": None,
        },
    }


@pytest.mark.parametrize(
    ["name", "error"],
    [
        pytest.param(
            "aa",
            {
                "context": {"min_length": 3},
                "input": "aa",
                "location": ["body", "new_name"],
                "message": "String should have at least 3 characters",
                "code": "string_too_short",
            },
            id="name_too_short",
        ),
        pytest.param(
            "a" * 129,
            {
                "context": {"max_length": 128},
                "input": "a" * 129,
                "location": ["body", "new_name"],
                "message": "String should have at most 128 characters",
                "code": "string_too_long",
            },
            id="name_too_long",
        ),
    ],
)
async def test_check_new_name_field_validation_on_copy_connection(
    client: AsyncClient,
    group_connection_and_group_developer_plus: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
    name: str,
    error: dict,
):
    role = group_connection_and_group_developer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"new_group_id": empty_group.id, "new_name": name},
    )

    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [error],
        },
    }


async def test_superuser_can_copy_connection_without_deleting_source(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
    empty_group: MockGroup,
    session: AsyncSession,
    settings: Settings,
):
    old_connection = await session.get(Connection, group_connection.id)
    old_auth_data = await session.get(AuthData, group_connection.id)
    old_credentials = decrypt_auth_data(old_auth_data.value, settings)

    new_connection_query = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    new_connection = (await session.scalars(new_connection_query)).one_or_none()
    assert not new_connection

    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": empty_group.id,
            "remove_source": False,
        },
    )

    assert response.status_code == 200, response.text

    # new connection with new name exist in target group
    new_connection = (await session.scalars(new_connection_query)).one()

    assert response.json() == {
        "id": new_connection.id,
        "group_id": empty_group.group.id,
        "name": old_connection.name,
        "description": old_connection.description,
        "type": old_connection.type,
        "connection_data": {
            "host": old_connection.data["host"],
            "port": old_connection.data["port"],
            "database_name": old_connection.data["database_name"],
            "additional_params": old_connection.data["additional_params"],
        },
        "auth_data": None,
    }

    new_auth_data = await session.get(AuthData, new_connection.id)
    assert new_auth_data is None

    # Check old (original) connection still exists
    session.expunge(old_connection)
    old_connection = await session.get(Connection, group_connection.id)
    assert old_connection is not None

    # Check old auth_data is unchanged
    session.expunge(old_auth_data)
    old_auth_data = await session.get(AuthData, group_connection.id)
    assert decrypt_auth_data(old_auth_data.value, settings) == old_credentials


async def test_superuser_can_copy_connection_and_delete_source(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
    empty_group: MockGroup,
    session: AsyncSession,
):
    old_connection = await session.get(Connection, group_connection.id)
    old_auth_data = await session.get(AuthData, group_connection.id)

    new_connection_query = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    new_connection = (await session.scalars(new_connection_query)).one_or_none()
    assert not new_connection

    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": empty_group.id,
            "remove_source": True,
        },
    )

    assert response.status_code == 200, response.text

    # new connection with new name exist in target group
    new_connection = (await session.scalars(new_connection_query)).one()

    assert response.json() == {
        "id": new_connection.id,
        "group_id": empty_group.group.id,
        "name": old_connection.name,
        "description": old_connection.description,
        "type": old_connection.type,
        "connection_data": {
            "host": old_connection.data["host"],
            "port": old_connection.data["port"],
            "database_name": old_connection.data["database_name"],
            "additional_params": old_connection.data["additional_params"],
        },
        "auth_data": None,
    }

    new_auth_data = await session.get(AuthData, new_connection.id)
    assert new_auth_data is None

    # Check old (original) connection was removed
    session.expunge(old_connection)
    old_connection = await session.get(Connection, group_connection.id)
    assert old_connection is None

    # Check old auth_data was removed
    session.expunge(old_auth_data)
    old_auth_data = await session.get(AuthData, group_connection.id)
    assert old_auth_data is None


async def test_unauthorized_user_cannot_copy_connection(
    client: AsyncClient,
    empty_group: MockGroup,
    group_connection: MockConnection,
):
    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        json={
            "new_group_id": empty_group.id,
        },
    )
    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Not authenticated",
            "details": None,
        },
    }


async def test_groupless_user_cannot_copy_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    empty_group: MockGroup,
    simple_user: MockUser,
):
    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }


async def test_other_group_member_cannot_copy_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    group: MockGroup,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)

    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group.group.id,
        },
    )
    assert response.status_code == 404, response.text
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }


async def test_not_in_both_groups_user_can_not_copy_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    empty_group: MockGroup,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)

    response = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_cannot_copy_connection_with_unknown_connection_error(
    client: AsyncClient,
    group_connection_and_group_developer_plus: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    role = group_connection_and_group_developer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    response = await client.post(
        "v1/connections/-1/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_superuser_cannot_copy_unknown_connection_error(
    client: AsyncClient,
    superuser: MockUser,
    empty_group: MockGroup,
):
    response = await client.post(
        "v1/connections/-1/copy_connection",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Connection not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_cannot_copy_connection_with_unknown_new_group_id_error(
    client: AsyncClient,
    group_connection_and_group_developer_plus: str,
    group_connection: MockConnection,
):
    role = group_connection_and_group_developer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    response = await client.post(
        f"v1/connections/{group_connection.connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": -1,
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text


async def test_superuser_cannot_copy_connection_with_unknown_new_group_id_error(
    client: AsyncClient,
    superuser: MockUser,
    group_connection: MockConnection,
):
    response = await client.post(
        f"v1/connections/{group_connection.connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": -1,
        },
    )

    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert response.status_code == 404, response.text
