import time

import pytest
import responses
from httpx import AsyncClient

from syncmaster.backend.settings import BackendSettings as Settings
from tests.mocks import MockUser
from tests.test_unit.test_auth.mocks.keycloak import (
    create_session_cookie,
    mock_keycloak_realm,
    mock_keycloak_well_known,
)

KEYCLOAK_PROVIDER = "syncmaster.backend.providers.auth.keycloak_provider.KeycloakAuthProvider"
pytestmark = [pytest.mark.asyncio, pytest.mark.backend]


@responses.activate
@pytest.mark.parametrize("settings", [{"auth": {"provider": KEYCLOAK_PROVIDER}}], indirect=True)
async def test_get_keycloak_user_unauthorized(client: AsyncClient):
    mock_keycloak_well_known(responses)

    response = await client.get("/v1/users/some_user_id")

    # redirect unauthorized user to Keycloak
    assert response.status_code == 307
    assert "protocol/openid-connect/auth?" in str(
        response.next_request.url,
    )


@responses.activate
@pytest.mark.parametrize("settings", [{"auth": {"provider": KEYCLOAK_PROVIDER}}], indirect=True)
async def test_get_keycloak_user_authorized(
    client: AsyncClient,
    simple_user: MockUser,
    settings: Settings,
    access_token_factory,
):
    payload = {
        "sub": str(simple_user.id),
        "preferred_username": simple_user.username,
        "email": simple_user.email,
        "given_name": simple_user.first_name,
        "middle_name": simple_user.middle_name,
        "family_name": simple_user.last_name,
        "exp": time.time() + 1000,
    }

    mock_keycloak_well_known(responses)
    mock_keycloak_realm(responses)

    session_cookie = create_session_cookie(payload, settings.server.session.secret_key)
    headers = {
        "Cookie": f"session={session_cookie}",
    }
    response = await client.get(
        f"/v1/users/{simple_user.id}",
        headers=headers,
    )

    assert response.status_code == 200
    assert response.json() == {
        "id": simple_user.id,
        "is_superuser": simple_user.is_superuser,
        "username": simple_user.username,
    }


@responses.activate
@pytest.mark.parametrize("settings", [{"auth": {"provider": KEYCLOAK_PROVIDER}}], indirect=True)
async def test_get_keycloak_deleted_user(
    client: AsyncClient,
    simple_user: MockUser,
    deleted_user: MockUser,
    settings: Settings,
):
    payload = {
        "sub": str(simple_user.id),
        "preferred_username": simple_user.username,
        "email": simple_user.email,
        "given_name": simple_user.first_name,
        "middle_name": simple_user.middle_name,
        "family_name": simple_user.last_name,
        "exp": time.time() + 1000,
    }

    mock_keycloak_well_known(responses)
    mock_keycloak_realm(responses)

    session_cookie = create_session_cookie(payload, settings.server.session.secret_key)
    headers = {
        "Cookie": f"session={session_cookie}",
    }
    response = await client.get(
        f"/v1/users/{deleted_user.id}",
        headers=headers,
    )
    assert response.status_code == 404
    assert response.json() == {
        "error": {
            "code": "not_found",
            "message": "User not found",
            "details": None,
        },
    }


@responses.activate
@pytest.mark.parametrize("settings", [{"auth": {"provider": KEYCLOAK_PROVIDER}}], indirect=True)
async def test_get_keycloak_user_inactive(
    client: AsyncClient,
    simple_user: MockUser,
    inactive_user: MockUser,
    settings: Settings,
):
    payload = {
        "sub": str(inactive_user.id),
        "preferred_username": inactive_user.username,
        "email": inactive_user.email,
        "given_name": inactive_user.first_name,
        "middle_name": inactive_user.middle_name,
        "family_name": inactive_user.last_name,
        "exp": time.time() + 1000,
    }

    mock_keycloak_well_known(responses)
    mock_keycloak_realm(responses)

    session_cookie = create_session_cookie(payload, settings.server.session.secret_key)
    headers = {
        "Cookie": f"session={session_cookie}",
    }

    response = await client.get(
        f"/v1/users/{simple_user.id}",
        headers=headers,
    )
    assert response.status_code == 403
    assert response.json() == {
        "error": {
            "code": "forbidden",
            "message": "You have no power here",
            "details": None,
        },
    }
