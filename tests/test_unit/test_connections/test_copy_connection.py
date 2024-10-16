import secrets

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.config import Settings
from syncmaster.db.models import AuthData, Connection
from syncmaster.db.repositories.utils import decrypt_auth_data
from tests.mocks import MockConnection, MockGroup, MockUser, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


@pytest.mark.parametrize("is_delete_source", [True, False])
async def test_maintainer_plus_can_copy_connection_with_delete_source(
    client: AsyncClient,
    session: AsyncSession,
    is_delete_source: bool,
    settings: Settings,
    group_connection: MockConnection,
    empty_group: MockGroup,
    group_connection_and_group_maintainer_plus: str,
):
    # Arrange
    role = group_connection_and_group_maintainer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    # Check: new connection does not exist and source connection not deleted
    query_current_row = select(Connection).where(Connection.id == group_connection.id)

    result_current_row = await session.scalars(query_current_row)
    current = result_current_row.one()

    query_current_creds = select(AuthData).where(AuthData.connection_id == group_connection.id)
    result_current_creds = await session.scalars(query_current_creds)
    current_cred = result_current_creds.one()

    curr_id = current.id

    assert decrypt_auth_data(current_cred.value, settings) == {
        "type": "postgres",
        "user": "user",
        "password": "password",
    }
    assert not current.is_deleted

    query_copy_not_exist = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    result_copy_not_exist = await session.scalars(query_copy_not_exist)
    row_copy_not_exist = result_copy_not_exist.one_or_none()

    assert not row_copy_not_exist

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
            "remove_source": is_delete_source,
        },
    )

    # Pre-Assert
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was copied",
    }
    assert result.status_code == 200

    await session.refresh(group_connection.connection)
    query_prev_row = select(Connection).where(Connection.id == curr_id)
    result_prev_row = await session.scalars(query_prev_row)
    origin = result_prev_row.one()

    q_creds_origin = select(AuthData).where(AuthData.connection_id == curr_id)
    creds_origin = await session.scalars(q_creds_origin)
    creds_origin = creds_origin.one()

    query_new_row = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    result_new_row = await session.scalars(query_new_row)
    new = result_new_row.one()  # connection was copied

    q_creds_new = select(AuthData).where(AuthData.connection_id == new.id)
    creds_new = await session.scalars(q_creds_new)
    creds_new = creds_new.one_or_none()

    # Assert
    assert origin.id == curr_id
    assert decrypt_auth_data(creds_origin.value, settings) == {
        "type": "postgres",
        "user": "user",
        "password": "password",
    }
    assert origin.is_deleted == is_delete_source
    assert not new.is_deleted
    assert not creds_new


@pytest.mark.parametrize("is_delete_source", [True, False])
async def test_superuser_can_copy_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    superuser: MockUser,
    empty_group: MockGroup,
    session: AsyncSession,
    is_delete_source: str,
    settings: Settings,
):
    # Arrange
    query_current_row = select(Connection).where(Connection.id == group_connection.id)
    result_current_row = await session.scalars(query_current_row)
    current = result_current_row.one()

    query_current_creds = select(AuthData).where(AuthData.connection_id == group_connection.id)
    result_current_creds = await session.scalars(query_current_creds)
    current_cred = result_current_creds.one()

    curr_id = current.id
    curr_group_id = current.group_id

    assert decrypt_auth_data(current_cred.value, settings) == {
        "type": "postgres",
        "user": "user",
        "password": "password",
    }
    assert not current.is_deleted

    query_copy_not_exist = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    result_copy_not_exist = await session.scalars(query_copy_not_exist)
    row_copy_not_exist = result_copy_not_exist.one_or_none()

    assert not row_copy_not_exist

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": empty_group.id,
            "remove_source": is_delete_source,
        },
    )

    # Pre-assert
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was copied",
    }
    assert result.status_code == 200

    query_prev_row = select(Connection).where(Connection.id == curr_id)
    result_prev_row = await session.scalars(query_prev_row)
    origin = result_prev_row.one()
    query_new_row = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    result_new_row = await session.scalars(query_new_row)
    new = result_new_row.one()  # copied

    # Assert
    await session.refresh(group_connection.connection)

    q_creds_origin = select(AuthData).where(AuthData.connection_id == origin.id)
    creds_origin = await session.scalars(q_creds_origin)
    creds_origin = creds_origin.one()

    q_creds_new = select(AuthData).where(AuthData.connection_id == new.id)
    creds_new = await session.scalars(q_creds_new)
    creds_new = creds_new.one_or_none()

    assert origin.id == curr_id
    assert origin.group_id == curr_group_id
    assert decrypt_auth_data(creds_origin.value, settings) == {
        "type": "postgres",
        "user": "user",
        "password": "password",
    }
    assert origin.is_deleted == is_delete_source
    assert not new.is_deleted
    assert not creds_new


async def test_unauthorized_user_cannot_copy_connection(
    client: AsyncClient,
    simple_user: MockUser,
    empty_group: MockGroup,
    group_connection: MockConnection,
):
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        json={
            "new_group_id": empty_group.id,
        },
    )
    assert result.status_code == 401
    assert result.json() == {
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
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {simple_user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )
    assert result.status_code == 404
    assert result.json() == {
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
    session: AsyncSession,
    settings: Settings,
    role_guest_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_guest_plus)

    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": group.group.id,
        },
    )
    assert result.status_code == 404
    assert result.json() == {
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
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
):
    # Arrange
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)

    query_current_row = select(Connection).where(Connection.id == group_connection.id)

    result_current_row = await session.scalars(query_current_row)
    current = result_current_row.one()

    query_current_creds = select(AuthData).where(AuthData.connection_id == group_connection.id)
    result_current_creds = await session.scalars(query_current_creds)
    current_cred = result_current_creds.one()

    assert decrypt_auth_data(current_cred.value, settings) == {
        "type": "postgres",
        "user": "user",
        "password": "password",
    }
    assert not current.is_deleted

    query_copy_not_exist = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    result_copy_not_exist = await session.scalars(query_copy_not_exist)
    row_copy_not_exist = result_copy_not_exist.one_or_none()

    assert not row_copy_not_exist

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_groupless_user_can_not_copy_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    group: MockGroup,
    empty_group: MockGroup,
    simple_user: MockUser,
    session: AsyncSession,
    settings: Settings,
    role_guest_plus: UserTestRoles,
):
    # Arrange
    user = simple_user

    query_current_row = select(Connection).where(Connection.id == group_connection.id)

    result_current_row = await session.scalars(query_current_row)
    current = result_current_row.one()

    query_current_creds = select(AuthData).where(AuthData.connection_id == group_connection.id)
    result_current_creds = await session.scalars(query_current_creds)
    current_cred = result_current_creds.one()

    assert decrypt_auth_data(current_cred.value, settings) == {
        "type": "postgres",
        "user": "user",
        "password": "password",
    }
    assert not current.is_deleted

    query_copy_not_exist = select(Connection).filter(
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    result_copy_not_exist = await session.scalars(query_copy_not_exist)
    row_copy_not_exist = result_copy_not_exist.one_or_none()

    assert not row_copy_not_exist

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
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


async def test_developer_plus_can_copy_connection_without_remove_source(
    client: AsyncClient,
    role_developer_plus: UserTestRoles,
    group_connection_and_group_developer_plus: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    # Arrange
    role = group_connection_and_group_developer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was copied",
    }


async def test_developer_plus_can_copy_connection_with_new_connection_name(
    client: AsyncClient,
    session: AsyncSession,
    role_developer_plus: UserTestRoles,
    group_connection_and_group_developer_plus: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    # Arrange
    role = group_connection_and_group_developer_plus
    user = group_connection.owner_group.get_member_of_role(role)
    new_name = f"{secrets.token_hex(5)}"

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"new_group_id": empty_group.id, "new_name": new_name},
    )

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was copied",
    }

    # new connection with new name exist in target group
    new_connection = await session.scalars(
        select(Connection).filter(
            Connection.name == new_name,
            Connection.group_id == empty_group.group.id,
        ),
    )
    conn_with_old_name = await session.scalars(
        select(Connection).filter(
            Connection.name == group_connection.connection.name,
            Connection.group_id == empty_group.group.id,
        ),
    )
    assert new_connection.one()
    assert not conn_with_old_name.one_or_none()


async def test_check_name_validation_copy_connection_with_new_connection_name(
    client: AsyncClient,
    session: AsyncSession,
    role_developer_plus: UserTestRoles,
    group_connection_and_group_developer_plus: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    # Arrange
    role = group_connection_and_group_developer_plus
    user = group_connection.owner_group.get_member_of_role(role)
    new_name = ""

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"new_group_id": empty_group.id, "new_name": new_name},
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "context": {"min_length": 1},
                    "input": "",
                    "location": ["body", "new_name"],
                    "message": "String should have at least 1 character",
                    "code": "string_too_short",
                },
            ],
        },
    }


async def test_maintainer_plus_cannot_copy_connection_with_same_name_in_new_group(
    client: AsyncClient,
    session: AsyncSession,
    settings: Settings,
    group_connection_with_same_name_maintainer_plus: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    # Arrange
    role = group_connection_with_same_name_maintainer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "conflict",
            "message": "The connection name already exists in the target group, please specify a new one",
            "details": None,
        },
    }


async def test_developer_below_can_not_copy_connection_with_remove_source(
    client: AsyncClient,
    role_developer_or_below: UserTestRoles,
    group_connection_and_group_developer_or_below: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    # Arrange
    role = group_connection_and_group_developer_or_below
    user = group_connection.owner_group.get_member_of_role(role)

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
            "remove_source": True,
        },
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


async def test_cannot_copy_connection_with_unknown_connection_error(
    client: AsyncClient,
    role_developer_plus: UserTestRoles,
    group_connection_and_group_developer_plus: str,
    group_connection: MockConnection,
    empty_group: MockGroup,
):
    # Arrange
    role = group_connection_and_group_developer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    # Act
    result = await client.post(
        "v1/connections/-1/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": empty_group.id,
        },
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


async def test_superuser_cannot_copy_unknown_connection_error(
    client: AsyncClient,
    superuser: MockUser,
    empty_group: MockGroup,
):
    # Act
    result = await client.post(
        "v1/connections/-1/copy_connection",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": empty_group.id,
        },
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


async def test_cannot_copy_connection_with_unknown_new_group_id_error(
    client: AsyncClient,
    role_developer_plus: UserTestRoles,
    group_connection_and_group_developer_plus: str,
    group_connection: MockConnection,
):
    # Arrange
    role = group_connection_and_group_developer_plus
    user = group_connection.owner_group.get_member_of_role(role)

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "new_group_id": -1,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404


async def test_superuser_cannot_copy_connection_with_unknown_new_group_id_error(
    client: AsyncClient,
    superuser: MockUser,
    group_connection: MockConnection,
):
    # Act
    result = await client.post(
        f"v1/connections/{group_connection.connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": -1,
        },
    )

    # Assert
    assert result.json() == {
        "error": {
            "code": "not_found",
            "message": "Group not found",
            "details": None,
        },
    }
    assert result.status_code == 404
