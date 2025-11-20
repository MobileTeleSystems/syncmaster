import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import AuthData, Connection
from syncmaster.db.repositories.utils import decrypt_auth_data
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockGroup, UserTestRoles

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.iceberg]


async def test_developer_plus_can_create_iceberg_rest_s3_direct_connection(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
    role_developer_plus: UserTestRoles,
):
    user = group.get_member_of_role(role_developer_plus)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "type": "iceberg",
            "connection_data": {
                "type": "iceberg_rest_s3_direct",
                "rest_catalog_url": "https://rest.domain.com",
                "s3_warehouse_path": "/some/warehouse",
                "s3_protocol": "http",
                "s3_host": "localhost",
                "s3_port": 9010,
                "s3_bucket": "some_bucket",
                "s3_region": "us-east-1",
                "s3_bucket_style": "path",
            },
            "auth_data": {
                "type": "iceberg_rest_basic_s3_basic",
                "rest_catalog_username": "user",
                "rest_catalog_password": "secret",
                "s3_access_key": "access_key",
                "s3_secret_key": "secret_key",
            },
        },
    )
    assert response.status_code == 200, response.text

    connection = (
        await session.scalars(
            select(Connection).filter_by(
                name="New connection",
            ),
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            ),
        )
    ).one()

    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert response.json() == {
        "id": connection.id,
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "type": connection.type,
        "connection_data": {
            "type": connection.data["type"],
            "rest_catalog_url": connection.data["rest_catalog_url"],
            "s3_warehouse_path": connection.data["s3_warehouse_path"],
            "s3_protocol": connection.data["s3_protocol"],
            "s3_host": connection.data["s3_host"],
            "s3_port": connection.data["s3_port"],
            "s3_bucket": connection.data["s3_bucket"],
            "s3_region": connection.data["s3_region"],
            "s3_bucket_style": connection.data["s3_bucket_style"],
            "s3_additional_params": connection.data["s3_additional_params"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "rest_catalog_username": decrypted["rest_catalog_username"],
            "s3_access_key": decrypted["s3_access_key"],
        },
    }


async def test_developer_plus_can_create_iceberg_rest_s3_delegated_connection(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
):
    user = group.get_member_of_role(UserTestRoles.Developer)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "type": "iceberg",
            "connection_data": {
                "type": "iceberg_rest_s3_delegated",
                "rest_catalog_url": "https://rest.domain.com",
                "s3_warehouse_name": "some-warehouse",
                "s3_access_delegation": "vended-credentials",
            },
            "auth_data": {
                "type": "iceberg_rest_basic",
                "rest_catalog_username": "user",
                "rest_catalog_password": "secret",
            },
        },
    )
    assert response.status_code == 200, response.text

    connection = (
        await session.scalars(
            select(Connection).filter_by(
                name="New connection",
            ),
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            ),
        )
    ).one()

    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert response.json() == {
        "id": connection.id,
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "type": connection.type,
        "connection_data": {
            "type": connection.data["type"],
            "rest_catalog_url": connection.data["rest_catalog_url"],
            "s3_warehouse_name": connection.data["s3_warehouse_name"],
            "s3_access_delegation": connection.data["s3_access_delegation"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "rest_catalog_username": decrypted["rest_catalog_username"],
        },
    }


async def test_developer_plus_can_create_iceberg_rest_s3_direct_connection_with_oauth2_client_credentials(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
):
    user = group.get_member_of_role(UserTestRoles.Developer)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "type": "iceberg",
            "connection_data": {
                "type": "iceberg_rest_s3_direct",
                "rest_catalog_url": "https://rest.domain.com",
                "s3_warehouse_path": "/some/warehouse",
                "s3_protocol": "http",
                "s3_host": "localhost",
                "s3_port": 9010,
                "s3_bucket": "some_bucket",
                "s3_region": "us-east-1",
                "s3_bucket_style": "path",
            },
            "auth_data": {
                "type": "iceberg_rest_oauth2_client_credentials_s3_basic",
                "rest_catalog_oauth2_client_id": "my_client_id",
                "rest_catalog_oauth2_client_secret": "my_client_secret",
                "rest_catalog_oauth2_scopes": ["catalog:read"],
                "rest_catalog_oauth2_audience": "iceberg-catalog",
                "rest_catalog_oauth2_token_endpoint": "https://oauth.example.com/token",
                "s3_access_key": "access_key",
                "s3_secret_key": "secret_key",
            },
        },
    )
    assert response.status_code == 200, response.text

    connection = (
        await session.scalars(
            select(Connection).filter_by(
                name="New connection",
            ),
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            ),
        )
    ).one()

    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert response.json() == {
        "id": connection.id,
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "type": connection.type,
        "connection_data": {
            "type": connection.data["type"],
            "rest_catalog_url": connection.data["rest_catalog_url"],
            "s3_warehouse_path": connection.data["s3_warehouse_path"],
            "s3_protocol": connection.data["s3_protocol"],
            "s3_host": connection.data["s3_host"],
            "s3_port": connection.data["s3_port"],
            "s3_bucket": connection.data["s3_bucket"],
            "s3_region": connection.data["s3_region"],
            "s3_bucket_style": connection.data["s3_bucket_style"],
            "s3_additional_params": connection.data["s3_additional_params"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "rest_catalog_oauth2_client_id": decrypted["rest_catalog_oauth2_client_id"],
            "rest_catalog_oauth2_scopes": decrypted["rest_catalog_oauth2_scopes"],
            "rest_catalog_oauth2_audience": decrypted["rest_catalog_oauth2_audience"],
            "rest_catalog_oauth2_resource": decrypted["rest_catalog_oauth2_resource"],
            "rest_catalog_oauth2_token_endpoint": decrypted["rest_catalog_oauth2_token_endpoint"],
            "s3_access_key": decrypted["s3_access_key"],
        },
    }


async def test_developer_plus_can_create_iceberg_rest_s3_delegated_connection_with_oauth2_client_credentials(
    client: AsyncClient,
    group: MockGroup,
    session: AsyncSession,
    settings: Settings,
):
    user = group.get_member_of_role(UserTestRoles.Developer)

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            "group_id": group.id,
            "name": "New connection",
            "description": "",
            "type": "iceberg",
            "connection_data": {
                "type": "iceberg_rest_s3_delegated",
                "rest_catalog_url": "https://rest.domain.com",
                "s3_warehouse_name": "some-warehouse",
                "s3_access_delegation": "vended-credentials",
            },
            "auth_data": {
                "type": "iceberg_rest_oauth2_client_credentials",
                "rest_catalog_oauth2_client_id": "my_client_id",
                "rest_catalog_oauth2_client_secret": "my_client_secret",
                "rest_catalog_oauth2_scopes": ["catalog:read"],
                "rest_catalog_oauth2_audience": "iceberg-catalog",
                "rest_catalog_oauth2_resource": "some_resource",
                "rest_catalog_oauth2_token_endpoint": "https://oauth.example.com/token",
            },
        },
    )
    assert response.status_code == 200, response.text

    connection = (
        await session.scalars(
            select(Connection).filter_by(
                name="New connection",
            ),
        )
    ).first()

    creds = (
        await session.scalars(
            select(AuthData).filter_by(
                connection_id=connection.id,
            ),
        )
    ).one()

    decrypted = decrypt_auth_data(creds.value, settings=settings)
    assert response.json() == {
        "id": connection.id,
        "group_id": connection.group_id,
        "name": connection.name,
        "description": connection.description,
        "type": connection.type,
        "connection_data": {
            "type": connection.data["type"],
            "rest_catalog_url": connection.data["rest_catalog_url"],
            "s3_warehouse_name": connection.data["s3_warehouse_name"],
            "s3_access_delegation": connection.data["s3_access_delegation"],
        },
        "auth_data": {
            "type": decrypted["type"],
            "rest_catalog_oauth2_client_id": decrypted["rest_catalog_oauth2_client_id"],
            "rest_catalog_oauth2_scopes": decrypted["rest_catalog_oauth2_scopes"],
            "rest_catalog_oauth2_audience": decrypted["rest_catalog_oauth2_audience"],
            "rest_catalog_oauth2_resource": decrypted["rest_catalog_oauth2_resource"],
            "rest_catalog_oauth2_token_endpoint": decrypted["rest_catalog_oauth2_token_endpoint"],
        },
    }


@pytest.mark.parametrize(
    ("auth_data"),
    [
        pytest.param(
            {
                "type": "iceberg_rest_basic",
                "rest_catalog_username": "user",
                "rest_catalog_password": "secret",
            },
            id="with_basic_auth",
        ),
        pytest.param(
            {
                "type": "iceberg_rest_oauth2_client_credentials",
                "rest_catalog_oauth2_client_id": "my_client_id",
                "rest_catalog_oauth2_client_secret": "my_client_secret",
                "rest_catalog_oauth2_scopes": ["catalog:read"],
                "rest_catalog_oauth2_audience": "iceberg-catalog",
                "rest_catalog_oauth2_resource": "some_resource",
                "rest_catalog_oauth2_token_endpoint": "https://oauth.example.com/token",
            },
            id="with_oauth2_client_credentials",
        ),
    ],
)
async def test_developer_plus_can_create_iceberg_rest_s3_direct_connection_without_credentials(
    client: AsyncClient,
    group: MockGroup,
    auth_data: dict,
):
    user = group.get_member_of_role(UserTestRoles.Developer)

    body = {
        "group_id": group.id,
        "name": "New connection",
        "description": "",
        "type": "iceberg",
        "connection_data": {
            "type": "iceberg_rest_s3_direct",
            "rest_catalog_url": "https://rest.domain.com",
            "s3_warehouse_path": "/some/warehouse",
            "s3_protocol": "http",
            "s3_host": "localhost",
            "s3_port": 9010,
            "s3_bucket": "some_bucket",
            "s3_region": "us-east-1",
            "s3_bucket_style": "path",
        },
        "auth_data": auth_data,
    }

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json=body,
    )
    assert response.status_code == 422, response.text

    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "location": ["body", "iceberg"],
                    "message": "Value error, Cannot create direct S3 connection without S3 credentials",
                    "code": "value_error",
                    "context": {},
                    "input": body,
                },
            ],
        },
    }


@pytest.mark.parametrize(
    ("auth_data"),
    [
        pytest.param(
            {
                "type": "iceberg_rest_basic_s3_basic",
                "rest_catalog_username": "user",
                "rest_catalog_password": "secret",
                "s3_access_key": "access_key",
                "s3_secret_key": "secret_key",
            },
            id="with_basic_auth",
        ),
        pytest.param(
            {
                "type": "iceberg_rest_oauth2_client_credentials_s3_basic",
                "rest_catalog_oauth2_client_id": "my_client_id",
                "rest_catalog_oauth2_client_secret": "my_client_secret",
                "rest_catalog_oauth2_scopes": ["catalog:read"],
                "rest_catalog_oauth2_audience": "iceberg-catalog",
                "rest_catalog_oauth2_token_endpoint": "https://oauth.example.com/token",
                "s3_access_key": "access_key",
                "s3_secret_key": "secret_key",
            },
            id="with_oauth2_client_credentials",
        ),
    ],
)
async def test_developer_plus_can_create_iceberg_rest_s3_delegated_connection_with_wrong_credentials(
    client: AsyncClient,
    group: MockGroup,
    auth_data: dict,
):
    user = group.get_member_of_role(UserTestRoles.Developer)

    body = {
        "group_id": group.id,
        "name": "New connection",
        "description": "",
        "type": "iceberg",
        "connection_data": {
            "type": "iceberg_rest_s3_delegated",
            "rest_catalog_url": "https://rest.domain.com",
            "s3_warehouse_path": "/some/warehouse",
            "s3_protocol": "http",
            "s3_host": "localhost",
            "s3_port": 9010,
            "s3_bucket": "some_bucket",
            "s3_region": "us-east-1",
            "s3_bucket_style": "path",
        },
        "auth_data": auth_data,
    }

    response = await client.post(
        "v1/connections",
        headers={"Authorization": f"Bearer {user.token}"},
        json=body,
    )
    assert response.status_code == 422, response.text

    assert response.json() == {
        "error": {
            "code": "invalid_request",
            "message": "Invalid request",
            "details": [
                {
                    "location": ["body", "iceberg"],
                    "message": "Value error, Cannot create delegated S3 connection with S3 credentials",
                    "code": "value_error",
                    "context": {},
                    "input": body,
                },
            ],
        },
    }
