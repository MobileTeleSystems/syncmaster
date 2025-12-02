import logging

import pytest
from dirty_equals import IsStr
from httpx import AsyncClient

from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockUser

pytestmark = [pytest.mark.asyncio, pytest.mark.server]

KEYCLOAK_AUTH_SETTINGS = {
    "auth": {
        "provider": "syncmaster.server.providers.auth.keycloak_provider.KeycloakAuthProvider",
        "keycloak": {
            "api_url": "http://localhost:8080/auth",
            "realm_name": "manually_created",
            "client_id": "manually_created",
            "client_secret": "generated_by_keycloak",
            "ui_callback_url": "http://localhost:3000/auth/callback",
            "scope": "email",
            "verify_ssl": False,
        },
        "cookie": {
            "secret_key": "generate_some_random_string",
            "max_age": 86400,
        },
    },
}


@pytest.mark.parametrize("settings", [KEYCLOAK_AUTH_SETTINGS], indirect=True)
async def test_keycloak_get_user_unauthorized(
    client: AsyncClient,
    simple_user: MockUser,
    mock_keycloak_well_known,
    mock_keycloak_realm,
):
    client.cookies.clear()
    response = await client.get(f"/v1/users/{simple_user.id}")

    # redirect unauthorized user to Keycloak
    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Please authorize using provided URL",
            "details": IsStr(regex=r".*protocol/openid-connect/auth\?.*"),
        },
    }


@pytest.mark.flaky
@pytest.mark.parametrize("settings", [KEYCLOAK_AUTH_SETTINGS], indirect=True)
async def test_keycloak_get_user_authorized(
    client: AsyncClient,
    simple_user: MockUser,
    settings: Settings,
    create_session_cookie,
    mock_keycloak_well_known,
    mock_keycloak_realm,
):
    client.cookies.clear()
    session_cookie = create_session_cookie(simple_user)
    response = await client.get(
        f"/v1/users/{simple_user.id}",
        cookies={"session": session_cookie},
    )

    assert response.cookies.get("session") == session_cookie
    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": simple_user.id,
        "is_superuser": simple_user.is_superuser,
        "username": simple_user.username,
    }


@pytest.mark.parametrize("settings", [KEYCLOAK_AUTH_SETTINGS], indirect=True)
async def test_keycloak_get_user_expired_access_token(
    caplog,
    client: AsyncClient,
    simple_user: MockUser,
    settings: Settings,
    create_session_cookie,
    mock_keycloak_well_known,
    mock_keycloak_realm,
    mock_keycloak_token_refresh,
):
    session_cookie = create_session_cookie(simple_user, expire_in_msec=-100000000)  # expired access token
    client.cookies = {"session": session_cookie}
    with caplog.at_level(logging.DEBUG):
        response = await client.get(f"/v1/users/{simple_user.id}")

    assert "Access token is invalid or expired" in caplog.text
    assert "Access token refreshed and decoded successfully" in caplog.text

    assert response.cookies.get("session") != session_cookie  # cookie is updated
    assert response.status_code == 200, response.text
    assert response.json() == {
        "id": simple_user.id,
        "is_superuser": simple_user.is_superuser,
        "username": simple_user.username,
    }


@pytest.mark.parametrize("settings", [KEYCLOAK_AUTH_SETTINGS], indirect=True)
async def test_keycloak_get_user_inactive(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    settings: Settings,
    create_session_cookie,
    mock_keycloak_well_known,
    mock_keycloak_realm,
):
    client.cookies = {"session": create_session_cookie(inactive_user)}
    response = await client.get(f"/v1/users/{simple_user.id}")
    assert response.status_code == 403, response.text
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


@pytest.mark.parametrize("settings", [KEYCLOAK_AUTH_SETTINGS], indirect=True)
async def test_keycloak_auth_callback(
    client: AsyncClient,
    settings: Settings,
    mock_keycloak_well_known,
    mock_keycloak_realm,
    mock_keycloak_token_refresh,
    caplog,
):
    client.cookies.clear()
    with caplog.at_level(logging.DEBUG):
        response = await client.get(
            "/v1/auth/callback",
            params={"code": "testcode"},
        )

    assert response.cookies.get("session"), caplog.text  # cookie is set
    assert response.status_code == 204, response.text


@pytest.mark.parametrize("settings", [KEYCLOAK_AUTH_SETTINGS], indirect=True)
async def test_keycloak_auth_logout(
    simple_user: MockUser,
    client: AsyncClient,
    settings: Settings,
    create_session_cookie,
    mock_keycloak_well_known,
    mock_keycloak_realm,
    mock_keycloak_token_refresh,
    mock_keycloak_logout,
):
    client.cookies = {"session": create_session_cookie(simple_user)}
    response = await client.get("/v1/auth/logout")
    assert response.status_code == 204, response.text
    assert response.cookies.get("session") is None
