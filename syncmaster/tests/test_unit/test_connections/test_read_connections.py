import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from tests.test_unit.utils import create_connection, create_credentials
from tests.utils import MockConnection, MockUser

from app.config import Settings
from app.db.repositories.utilites import decrypt_auth_data

pytestmark = [pytest.mark.asyncio]


async def test_unauthorized_user_cannot_read_connections(client: AsyncClient):
    result = await client.get("v1/connections")
    assert result.status_code == 401
    assert result.json() == {
        "ok": False,
        "status_code": 401,
        "message": "Not authenticated",
    }


async def test_user_can_read_own_connections(
    client: AsyncClient,
    simple_user: MockUser,
    session: AsyncSession,
    settings: Settings,
):
    result = await client.get(
        "v1/connections", headers={"Authorization": f"Bearer {simple_user.token}"}
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 0,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [],
    }

    simple_user_connection = await create_connection(
        session=session,
        name="new_connection",
        user_id=simple_user.id,
    )

    creds = await create_credentials(
        session=session,
        settings=settings,
        connection_id=simple_user_connection.id,
    )

    result_witn_connection = await client.get(
        "v1/connections", headers={"Authorization": f"Bearer {simple_user.token}"}
    )
    assert result_witn_connection.status_code == 200
    assert result_witn_connection.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 1,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": simple_user_connection.id,
                "description": simple_user_connection.description,
                "group_id": simple_user_connection.group_id,
                "user_id": simple_user_connection.user_id,
                "name": simple_user_connection.name,
                "connection_data": {
                    "type": simple_user_connection.data["type"],
                    "database_name": simple_user_connection.data["database_name"],
                    "host": simple_user_connection.data["host"],
                    "port": simple_user_connection.data["port"],
                    "additional_params": simple_user_connection.data[
                        "additional_params"
                    ],
                },
                "auth_data": {
                    "type": decrypt_auth_data(creds.value, settings=settings)["type"],
                    "user": decrypt_auth_data(creds.value, settings=settings)["user"],
                },
            },
        ],
    }


async def test_group_admin_can_read_connections(
    client: AsyncClient,
    simple_user: MockUser,
    group_connection: MockConnection,
    settings: Settings,
):
    result = await client.get(
        "v1/connections", headers={"Authorization": f"Bearer {simple_user.token}"}
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 0,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [],
    }

    connection_owner = group_connection.owner_group.admin
    result = await client.get(
        "v1/connections", headers={"Authorization": f"Bearer {connection_owner.token}"}
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 1,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": group_connection.id,
                "description": group_connection.description,
                "group_id": group_connection.group_id,
                "user_id": group_connection.user_id,
                "name": group_connection.name,
                "connection_data": {
                    "type": group_connection.data["type"],
                    "host": group_connection.data["host"],
                    "port": group_connection.data["port"],
                    "database_name": group_connection.data["database_name"],
                    "additional_params": group_connection.data["additional_params"],
                },
                "auth_data": {
                    "type": group_connection.credentials.value["type"],
                    "user": group_connection.credentials.value["user"],
                },
            },
        ],
    }


async def test_superuser_can_read_all_connections(
    client: AsyncClient,
    superuser: MockUser,
    user_connection: MockConnection,
    group_connection: MockConnection,
):
    result = await client.get(
        "v1/connections", headers={"Authorization": f"Bearer {superuser.token}"}
    )
    assert result.status_code == 200
    assert result.json() == {
        "meta": {
            "page": 1,
            "pages": 1,
            "total": 2,
            "page_size": 20,
            "has_next": False,
            "has_previous": False,
            "next_page": None,
            "previous_page": None,
        },
        "items": [
            {
                "id": group_connection.id,
                "description": group_connection.description,
                "group_id": group_connection.group_id,
                "user_id": group_connection.user_id,
                "name": group_connection.name,
                "connection_data": {
                    "type": group_connection.data["type"],
                    "host": group_connection.data["host"],
                    "port": group_connection.data["port"],
                    "database_name": group_connection.data["database_name"],
                    "additional_params": group_connection.data["additional_params"],
                },
                "auth_data": {
                    "type": group_connection.credentials.value["type"],
                    "user": group_connection.credentials.value["user"],
                },
            },
            {
                "id": user_connection.id,
                "description": user_connection.description,
                "group_id": user_connection.group_id,
                "user_id": user_connection.user_id,
                "name": user_connection.name,
                "connection_data": {
                    "type": user_connection.data["type"],
                    "host": user_connection.data["host"],
                    "port": user_connection.data["port"],
                    "database_name": user_connection.data["database_name"],
                    "additional_params": user_connection.data["additional_params"],
                },
                "auth_data": {
                    "type": group_connection.credentials.value["type"],
                    "user": group_connection.credentials.value["user"],
                },
            },
        ],
    }
