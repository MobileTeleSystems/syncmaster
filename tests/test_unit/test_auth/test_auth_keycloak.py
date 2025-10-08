import logging

import pytest
import responses
from dirty_equals import IsStr
from httpx import AsyncClient

from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockUser

KEYCLOAK_PROVIDER = "syncmaster.server.providers.auth.keycloak_provider.KeycloakAuthProvider"
pytestmark = [pytest.mark.asyncio, pytest.mark.server]


@responses.activate
@pytest.mark.parametrize(
    "settings",
    [
        {
            "auth": {
                "provider": KEYCLOAK_PROVIDER,
            },
        },
    ],
    indirect=True,
)
async def test_keycloak_get_user_unauthorized(client: AsyncClient, mock_keycloak_well_known):
    response = await client.get("/v1/users/some_user_id")

    # redirect unauthorized user to Keycloak
    assert response.status_code == 401, response.text
    assert response.json() == {
        "error": {
            "code": "unauthorized",
            "message": "Please authorize using provided URL",
            "details": IsStr(regex=r".*protocol/openid-connect/auth\?.*"),
        },
    }


@responses.activate
@pytest.mark.flaky
@pytest.mark.parametrize(
    "settings",
    [
        {
            "auth": {
                "provider": KEYCLOAK_PROVIDER,
            },
        },
    ],
    indirect=True,
)
async def test_keycloak_get_user_authorized(
    client: AsyncClient,
    simple_user: MockUser,
    settings: Settings,
    create_session_cookie,
    mock_keycloak_well_known,
    mock_keycloak_realm,
):
    session_cookie = create_session_cookie(simple_user)
    headers = {
        "Cookie": f"session={session_cookie}",
    }
    response = await client.get(
        f"/v1/users/{simple_user.id}",
        headers=headers,
    )

    assert response.cookies.get("session") == session_cookie
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "id": simple_user.id,
        "is_superuser": simple_user.is_superuser,
        "username": simple_user.username,
    }


@responses.activate
@pytest.mark.parametrize(
    "settings",
    [
        {
            "auth": {
                "provider": KEYCLOAK_PROVIDER,
            },
        },
    ],
    indirect=True,
)
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
    headers = {
        "Cookie": f"session={session_cookie}",
    }

    with caplog.at_level(logging.DEBUG):
        response = await client.get(
            f"/v1/users/{simple_user.id}",
            headers=headers,
        )

    assert "Access token is invalid or expired" in caplog.text
    assert "Access token refreshed and decoded successfully" in caplog.text

    assert response.cookies.get("session") != session_cookie  # cookie is updated
    assert response.status_code == 200, response.json()
    assert response.json() == {
        "id": simple_user.id,
        "is_superuser": simple_user.is_superuser,
        "username": simple_user.username,
    }


@responses.activate
@pytest.mark.parametrize(
    "settings",
    [
        {
            "auth": {
                "provider": KEYCLOAK_PROVIDER,
            },
        },
    ],
    indirect=True,
)
async def test_keycloak_get_user_inactive(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    settings: Settings,
    create_session_cookie,
    mock_keycloak_well_known,
    mock_keycloak_realm,
):
    session_cookie = create_session_cookie(inactive_user)
    headers = {
        "Cookie": f"session={session_cookie}",
    }

    response = await client.get(
        f"/v1/users/{simple_user.id}",
        headers=headers,
    )
    assert response.status_code == 403, response.json()
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }


@responses.activate
@pytest.mark.parametrize(
    "settings",
    [
        {
            "auth": {
                "provider": KEYCLOAK_PROVIDER,
            },
        },
    ],
    indirect=True,
)
async def test_keycloak_auth_callback(
    client: AsyncClient,
    settings: Settings,
    mock_keycloak_well_known,
    mock_keycloak_realm,
    mock_keycloak_token_refresh,
    caplog,
):
    with caplog.at_level(logging.DEBUG):
        response = await client.get(
            "/v1/auth/callback",
            params={"code": "testcode"},
        )

    assert response.cookies.get("session"), caplog.text  # cookie is set
    assert response.status_code == 204, response.json()
