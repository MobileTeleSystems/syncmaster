import pytest
from httpx import AsyncClient

from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockUser

pytestmark = [pytest.mark.asyncio, pytest.mark.server]

OAUTH2GATEWAY_AUTH_SETTINGS = {
    "auth": {
        "provider": "syncmaster.server.providers.auth.oauth2_gateway_provider.OAuth2GatewayProvider",
        "keycloak": {
            "server_url": "http://localhost:8080",
            "realm_name": "manually_created",
            "client_id": "manually_created",
            "client_secret": "generated_by_keycloak",
            "redirect_uri": "http://localhost:3000/auth/callback",
            "scope": "email",
            "verify_ssl": False,
        },
    },
}


@pytest.mark.parametrize("settings", [OAUTH2GATEWAY_AUTH_SETTINGS], indirect=True)
async def test_get_keycloak_token_active(
    client: AsyncClient,
    simple_user: MockUser,
    settings: Settings,
    mock_keycloak_introspect_token,
):

    mock_keycloak_introspect_token(simple_user)

    headers = {
        "Authorization": "Bearer token",
    }
    response = await client.get(
        f"/v1/users/{simple_user.id}",
        headers=headers,
    )

    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": simple_user.id,
        "is_superuser": simple_user.is_superuser,
        "username": simple_user.username,
    }


@pytest.mark.parametrize("settings", [OAUTH2GATEWAY_AUTH_SETTINGS], indirect=True)
async def test_get_keycloak_token_inactive(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    settings: Settings,
    mock_keycloak_introspect_token,
):
    mock_keycloak_introspect_token(inactive_user)

    headers = {
        "Authorization": "Bearer token",
    }

    response = await client.get(
        f"/v1/users/{simple_user.id}",
        headers=headers,
    )
    assert response.status_code == 401, response.text
    assert response.json() == {"error": {"code": "unauthorized", "details": None, "message": "Not authenticated"}}
