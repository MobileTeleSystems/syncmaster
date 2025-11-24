import pytest
from httpx import AsyncClient

from tests.mocks import MockConnection, UserTestRoles
from tests.test_unit.utils import fetch_connection_json

pytestmark = [pytest.mark.asyncio, pytest.mark.server, pytest.mark.iceberg]


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "iceberg",
            {
                "type": "iceberg_rest_s3_direct",
                "rest_catalog_url": "http://domain.com:8000",
                "s3_warehouse_path": "/some/warehouse",
                "s3_protocol": "http",
                "s3_host": "localhost",
                "s3_port": 9010,
                "s3_bucket": "some_bucket",
                "s3_region": "us-east-1",
                "s3_bucket_style": "path",
            },
            {
                "type": "iceberg_rest_bearer_s3_basic",
                "rest_catalog_token": "token",
                "s3_access_key": "access_key",
                "s3_secret_key": "secret_key",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_iceberg_rest_s3_direct_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    response = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            **connection_json,
            "type": group_connection.type,
            "connection_data": {
                "type": "iceberg_rest_s3_direct",
                "rest_catalog_url": "http://rest.domain.com:8000",
                "s3_warehouse_path": "/some/new/warehouse",
                "s3_protocol": "https",
                "s3_host": "s3.domain.com",
                "s3_bucket": "new_bucket",
                "s3_region": "us-east-2",
                "s3_bucket_style": "domain",
            },
            "auth_data": {
                "type": "iceberg_rest_bearer_s3_basic",
                "rest_catalog_token": "new_token",
                "s3_access_key": "new_access_key",
            },
        },
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
            "type": "iceberg_rest_s3_direct",
            "rest_catalog_url": "http://rest.domain.com:8000",
            "s3_warehouse_path": "/some/new/warehouse",
            "s3_protocol": "https",
            "s3_host": "s3.domain.com",
            "s3_port": None,
            "s3_bucket": "new_bucket",
            "s3_region": "us-east-2",
            "s3_bucket_style": "domain",
            "s3_additional_params": {},
        },
        "auth_data": {
            "type": group_connection.credentials.value["type"],
            "s3_access_key": "new_access_key",
        },
    }


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "iceberg",
            {
                "type": "iceberg_rest_s3_delegated",
                "rest_catalog_url": "http://domain.com:8000",
                "s3_warehouse_path": "some-warehouse",
                "s3_access_delegation": "vended-credentials",
            },
            {
                "type": "iceberg_rest_bearer",
                "rest_catalog_token": "token",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_iceberg_rest_s3_delegated_connection(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    response = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            **connection_json,
            "type": group_connection.type,
            "connection_data": {
                "type": "iceberg_rest_s3_delegated",
                "rest_catalog_url": "http://rest.domain.com:8000",
                "s3_warehouse_name": "some-new-warehouse",
                "s3_access_delegation": "remote-signing",
            },
            "auth_data": {
                "type": "iceberg_rest_bearer",
                "rest_catalog_token": "new_token",
            },
        },
    )

    assert response.status_code == 200, response.json()
    assert response.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
            "type": "iceberg_rest_s3_delegated",
            "rest_catalog_url": "http://rest.domain.com:8000",
            "s3_warehouse_name": "some-new-warehouse",
            "s3_access_delegation": "remote-signing",
        },
        "auth_data": {
            "type": "iceberg_rest_bearer",
        },
    }


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "iceberg",
            {
                "type": "iceberg_rest_s3_direct",
                "rest_catalog_url": "http://domain.com:8000",
                "s3_warehouse_path": "/some/warehouse",
                "s3_protocol": "http",
                "s3_host": "localhost",
                "s3_port": 9010,
                "s3_bucket": "some_bucket",
                "s3_region": "us-east-1",
                "s3_bucket_style": "path",
            },
            {
                "type": "iceberg_rest_oauth2_client_credentials_s3_basic",
                "rest_catalog_oauth2_client_id": "my_client_id",
                "rest_catalog_oauth2_client_secret": "my_client_secret",
                "rest_catalog_oauth2_scopes": ["catalog:read"],
                "rest_catalog_oauth2_audience": "iceberg-catalog",
                "rest_catalog_oauth2_resource": "some-old-resource",
                "rest_catalog_oauth2_token_endpoint": "https://oauth.example.com/token",
                "s3_access_key": "access_key",
                "s3_secret_key": "secret_key",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_iceberg_rest_s3_direct_connection_with_oauth2_client_credentials(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    response = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            **connection_json,
            "type": group_connection.type,
            "connection_data": {
                "type": "iceberg_rest_s3_direct",
                "rest_catalog_url": "http://rest.domain.com:8000",
                "s3_warehouse_path": "/some/new/warehouse",
                "s3_protocol": "https",
                "s3_host": "s3.domain.com",
                "s3_bucket": "new_bucket",
                "s3_region": "us-east-2",
                "s3_bucket_style": "domain",
            },
            "auth_data": {
                "type": "iceberg_rest_oauth2_client_credentials_s3_basic",
                "rest_catalog_oauth2_client_id": "my_new_client_id",
                "rest_catalog_oauth2_client_secret": "my_new_client_secret",
                "rest_catalog_oauth2_scopes": ["catalog:write"],
                "rest_catalog_oauth2_audience": "iceberg-new-catalog",
                "rest_catalog_oauth2_resource": "iceberg-new-resource",
                "rest_catalog_oauth2_token_endpoint": "https://oauth.new.example.com/token",
                "s3_access_key": "new_access_key",
                "s3_secret_key": "new_secret_key",
            },
        },
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
            "type": "iceberg_rest_s3_direct",
            "rest_catalog_url": "http://rest.domain.com:8000",
            "s3_warehouse_path": "/some/new/warehouse",
            "s3_protocol": "https",
            "s3_host": "s3.domain.com",
            "s3_port": None,
            "s3_bucket": "new_bucket",
            "s3_region": "us-east-2",
            "s3_bucket_style": "domain",
            "s3_additional_params": {},
        },
        "auth_data": {
            "type": "iceberg_rest_oauth2_client_credentials_s3_basic",
            "rest_catalog_oauth2_client_id": "my_new_client_id",
            "rest_catalog_oauth2_scopes": ["catalog:write"],
            "rest_catalog_oauth2_audience": "iceberg-new-catalog",
            "rest_catalog_oauth2_resource": "iceberg-new-resource",
            "rest_catalog_oauth2_token_endpoint": "https://oauth.new.example.com/token",
            "s3_access_key": "new_access_key",
        },
    }


@pytest.mark.parametrize(
    "connection_type,create_connection_data,create_connection_auth_data",
    [
        (
            "iceberg",
            {
                "type": "iceberg_rest_s3_delegated",
                "rest_catalog_url": "http://domain.com:8000",
                "s3_warehouse_path": "some-warehouse",
                "s3_access_delegation": "vended-credentials",
            },
            {
                "type": "iceberg_rest_oauth2_client_credentials",
                "rest_catalog_oauth2_client_id": "my_client_id",
                "rest_catalog_oauth2_client_secret": "my_new_client_secret",
                "rest_catalog_oauth2_scopes": ["catalog:read"],
                "rest_catalog_oauth2_audience": "iceberg-catalog",
                "rest_catalog_oauth2_resource": "some-old-resource",
                "rest_catalog_oauth2_token_endpoint": "https://oauth.example.com/token",
            },
        ),
    ],
    indirect=["create_connection_data", "create_connection_auth_data"],
)
async def test_developer_plus_can_update_iceberg_rest_s3_delegated_connection_with_oauth2_client_credentials(
    client: AsyncClient,
    group_connection: MockConnection,
    role_developer_plus: UserTestRoles,
):
    user = group_connection.owner_group.get_member_of_role(role_developer_plus)
    connection_json = await fetch_connection_json(client, user.token, group_connection)

    response = await client.put(
        f"v1/connections/{group_connection.id}",
        headers={"Authorization": f"Bearer {user.token}"},
        json={
            **connection_json,
            "type": group_connection.type,
            "connection_data": {
                "type": "iceberg_rest_s3_delegated",
                "rest_catalog_url": "http://rest.domain.com:8000",
                "s3_warehouse_name": "some-new-warehouse",
                "s3_access_delegation": "remote-signing",
            },
            "auth_data": {
                "type": "iceberg_rest_oauth2_client_credentials",
                "rest_catalog_oauth2_client_id": "my_new_client_id",
                "rest_catalog_oauth2_client_secret": "my_new_client_secret",
                "rest_catalog_oauth2_scopes": ["catalog:write"],
                "rest_catalog_oauth2_audience": "iceberg-new-catalog",
                "rest_catalog_oauth2_resource": "iceberg-new-resource",
                "rest_catalog_oauth2_token_endpoint": "https://oauth.new.example.com/token",
            },
        },
    )

    assert response.status_code == 200, response.json()
    assert response.json() == {
        "id": group_connection.id,
        "name": group_connection.name,
        "description": group_connection.description,
        "group_id": group_connection.group_id,
        "type": group_connection.type,
        "connection_data": {
            "type": "iceberg_rest_s3_delegated",
            "rest_catalog_url": "http://rest.domain.com:8000",
            "s3_warehouse_name": "some-new-warehouse",
            "s3_access_delegation": "remote-signing",
        },
        "auth_data": {
            "type": "iceberg_rest_oauth2_client_credentials",
            "rest_catalog_oauth2_client_id": "my_new_client_id",
            "rest_catalog_oauth2_scopes": ["catalog:write"],
            "rest_catalog_oauth2_audience": "iceberg-new-catalog",
            "rest_catalog_oauth2_resource": "iceberg-new-resource",
            "rest_catalog_oauth2_token_endpoint": "https://oauth.new.example.com/token",
        },
    }
