import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from tests.utils import MockConnection, MockGroup, MockUser

from app.config import Settings
from app.db.models import AuthData, Connection
from app.db.repositories.utilites import decrypt_auth_data

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_change_owner_of_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    simple_user: MockUser,
    group_connection: MockConnection,
):
    for connection in user_connection, group_connection:
        result = await client.post(
            f"v1/connections/{connection.id}/copy_connection",
            json={
                "new_user_id": simple_user.id,
            },
        )
        assert result.status_code == 401
        assert result.json() == {
            "ok": False,
            "status_code": 401,
            "message": "Not authenticated",
        }


async def test_simple_user_cannot_change_owner_of_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    group_connection: MockConnection,
    simple_user: MockUser,
):
    for connection in user_connection, group_connection:
        result = await client.post(
            f"v1/connections/{connection.id}/copy_connection",
            headers={"Authorization": f"Bearer {simple_user.token}"},
            json={
                "new_user_id": simple_user.id,
            },
        )
        assert result.status_code == 404
        assert result.json() == {
            "ok": False,
            "status_code": 404,
            "message": "Connection not found",
        }


async def test_group_member_cannot_change_owner_of_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    group_connection: MockConnection,
):
    member = group_connection.owner_group.members[0]
    for connection in user_connection, group_connection:
        result = await client.post(
            f"v1/connections/{connection.id}/copy_connection",
            headers={"Authorization": f"Bearer {member.token}"},
            json={
                "new_user_id": member.id,
            },
        )
        assert result.status_code == 404
        assert result.json() == {
            "ok": False,
            "status_code": 404,
            "message": "Connection not found",
        }


async def test_group_admin_cannot_change_owner_of_user_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    user_connection: MockConnection,
    simple_user: MockUser,
):
    admin = group_connection.owner_group.admin
    result = await client.post(
        f"v1/connections/{user_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={
            "new_user_id": simple_user.id,
        },
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


@pytest.mark.parametrize("is_delete_source", [True, False])
async def test_admin_can_copy_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    simple_user: MockUser,
    session: AsyncSession,
    is_delete_source: bool,
    settings: Settings,
):
    # Arrange
    admin = group_connection.owner_group.admin

    query_current_row = select(Connection).where(Connection.id == group_connection.id)
    result_current_row = await session.scalars(query_current_row)
    current = result_current_row.one()

    query_current_creds = select(AuthData).where(
        AuthData.connection_id == group_connection.id
    )
    result_current_creds = await session.scalars(query_current_creds)
    current_cred = result_current_creds.one()

    curr_id = current.id

    assert current.user_id is None
    assert decrypt_auth_data(current_cred.value, settings) == {
        "type": "postgres",
        "user": "user",
        "password": "password",
    }
    assert not current.is_deleted

    query_copy_not_exist = select(Connection).filter(
        Connection.user_id == simple_user.id,
        Connection.group_id.is_(None),
        Connection.name == group_connection.name,
    )
    result_copy_not_exist = await session.scalars(query_copy_not_exist)
    row_copy_not_exist = result_copy_not_exist.one_or_none()

    assert not row_copy_not_exist

    # Act
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {admin.token}"},
        json={
            "new_user_id": simple_user.id,
            "remove_source": is_delete_source,
        },
    )
    await session.refresh(group_connection.connection)
    query_prev_row = select(Connection).where(Connection.id == curr_id)
    result_prev_row = await session.scalars(query_prev_row)
    origin = result_prev_row.one()

    q_creds_origin = select(AuthData).where(AuthData.connection_id == curr_id)
    creds_origin = await session.scalars(q_creds_origin)
    creds_origin = creds_origin.one()

    query_new_row = select(Connection).filter(
        Connection.user_id == simple_user.id,
        Connection.group_id.is_(None),
        Connection.name == group_connection.name,
    )
    result_new_row = await session.scalars(query_new_row)
    new = result_new_row.one()

    q_creds_new = select(AuthData).where(AuthData.connection_id == new.id)
    creds_new = await session.scalars(q_creds_new)
    creds_new = creds_new.one_or_none()

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was copied.",
    }

    assert origin.id == curr_id
    assert origin.user_id is None
    assert decrypt_auth_data(creds_origin.value, settings) == {
        "type": "postgres",
        "user": "user",
        "password": "password",
    }
    assert origin.is_deleted == is_delete_source
    assert not new.is_deleted
    assert not creds_new


async def test_other_admin_cannot_change_owner_of_group_connection(
    client: AsyncClient, group_connection: MockConnection, empty_group: MockGroup
):
    result = await client.post(
        f"v1/connections/{group_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {empty_group.admin.token}"},
        json={
            "new_user_id": empty_group.admin.id,
        },
    )
    assert result.status_code == 404
    assert result.json() == {
        "ok": False,
        "status_code": 404,
        "message": "Connection not found",
    }


@pytest.mark.parametrize("is_delete_source", [True, False])
async def test_superuser_can_copy_user_connection(
    client: AsyncClient,
    user_connection: MockConnection,
    superuser: MockUser,
    empty_group: MockGroup,
    session: AsyncSession,
    is_delete_source: bool,
    settings: Settings,
):
    # Arrange
    query_current_row = select(Connection).where(Connection.id == user_connection.id)
    query_current_creds = select(AuthData).where(
        AuthData.connection_id == user_connection.id
    )
    result_current_creds = await session.scalars(query_current_creds)
    current_cred = result_current_creds.one()
    result_current_row = await session.scalars(query_current_row)
    current = result_current_row.one()

    curr_id = current.id

    assert current.group_id is None
    assert decrypt_auth_data(current_cred.value, settings) == {
        "type": "postgres",
        "user": "user",
        "password": "password",
    }
    assert not current.is_deleted

    query_copy_not_exist = select(Connection).filter(
        Connection.user_id.is_(None),
        Connection.group_id == empty_group.id,
        Connection.name == user_connection.name,
    )
    result_copy_not_exist = await session.scalars(query_copy_not_exist)
    row_copy_not_exist = result_copy_not_exist.one_or_none()

    assert not row_copy_not_exist

    # Act
    result = await client.post(
        f"v1/connections/{user_connection.id}/copy_connection",
        headers={"Authorization": f"Bearer {superuser.token}"},
        json={
            "new_group_id": empty_group.id,
            "remove_source": is_delete_source,
        },
    )

    query_prev_row = select(Connection).where(Connection.id == curr_id)
    result_prev_row = await session.scalars(query_prev_row)
    origin = result_prev_row.one()
    query_new_row = select(Connection).filter(
        Connection.user_id.is_(None),
        Connection.group_id == empty_group.id,
        Connection.name == user_connection.name,
    )
    result_new_row = await session.scalars(query_new_row)
    new = result_new_row.one()

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was copied.",
    }
    await session.refresh(user_connection.connection)

    assert origin.id == curr_id
    assert origin.group_id == None

    q_creds_origin = select(AuthData).where(AuthData.connection_id == origin.id)
    creds_origin = await session.scalars(q_creds_origin)
    creds_origin = creds_origin.one()

    q_creds_new = select(AuthData).where(AuthData.connection_id == new.id)
    creds_new = await session.scalars(q_creds_new)
    creds_new = creds_new.one_or_none()

    assert decrypt_auth_data(creds_origin.value, settings) == {
        "type": "postgres",
        "user": "user",
        "password": "password",
    }
    assert origin.is_deleted == is_delete_source
    assert not new.is_deleted
    assert not creds_new


@pytest.mark.parametrize("is_delete_source", [True, False])
async def test_superuser_can_change_owner_of_group_connection(
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

    query_current_creds = select(AuthData).where(
        AuthData.connection_id == group_connection.id
    )
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
        Connection.user_id.is_(None),
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

    query_prev_row = select(Connection).where(Connection.id == curr_id)
    result_prev_row = await session.scalars(query_prev_row)
    origin = result_prev_row.one()
    query_new_row = select(Connection).filter(
        Connection.user_id.is_(None),
        Connection.group_id == empty_group.id,
        Connection.name == group_connection.name,
    )
    result_new_row = await session.scalars(query_new_row)
    new = result_new_row.one()

    # Assert
    assert result.status_code == 200
    assert result.json() == {
        "ok": True,
        "status_code": 200,
        "message": "Connection was copied.",
    }
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
