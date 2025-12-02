import json
import time
from base64 import b64encode

import jwt
import pytest
import pytest_asyncio
import respx
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)
from itsdangerous import TimestampSigner


@pytest.fixture(scope="session")
def rsa_keys():
    # create private & public keys to emulate Keycloak signing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=Encoding.PEM,
        format=PrivateFormat.PKCS8,
        encryption_algorithm=NoEncryption(),
    )
    public_key = private_key.public_key()

    return {
        "private_key": private_key,
        "private_pem": private_pem,
        "public_key": public_key,
    }


def get_public_key_pem(public_key):
    public_pem = public_key.public_bytes(
        encoding=Encoding.PEM,
        format=PublicFormat.SubjectPublicKeyInfo,
    )
    public_pem_str = public_pem.decode("utf-8")
    public_pem_str = public_pem_str.replace("-----BEGIN PUBLIC KEY-----\n", "")
    public_pem_str = public_pem_str.replace("-----END PUBLIC KEY-----\n", "")
    public_pem_str = public_pem_str.replace("\n", "")
    return public_pem_str


@pytest.fixture
def create_session_cookie(rsa_keys, settings):
    def _create_session_cookie(user, expire_in_msec=60000) -> str:
        private_pem = rsa_keys["private_pem"]
        cookie_settings = settings.auth.model_dump()["cookie"]
        session_secret_key = cookie_settings["secret_key"]

        payload = {
            "sub": str(user.id),
            "preferred_username": user.username,
            "email": user.email,
            "given_name": user.first_name,
            "middle_name": user.middle_name,
            "family_name": user.last_name,
            "exp": int(time.time()) + (expire_in_msec / 1000),
        }

        access_token = jwt.encode(payload, private_pem, algorithm="RS256")
        refresh_token = "mock_refresh_token"

        session_data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
        }

        signer = TimestampSigner(session_secret_key)
        json_bytes = json.dumps(session_data).encode("utf-8")
        base64_bytes = b64encode(json_bytes)
        signed_data = signer.sign(base64_bytes)
        session_cookie = signed_data.decode("utf-8")

        return session_cookie

    return _create_session_cookie


@pytest_asyncio.fixture
async def mock_keycloak_api(settings):  # noqa: F811
    keycloak_settings = settings.auth.model_dump()["keycloak"]
    api_url = keycloak_settings["api_url"]

    async with respx.mock(base_url=api_url, assert_all_called=False) as respx_mock:
        yield respx_mock


@pytest.fixture
def mock_keycloak_well_known(settings, mock_keycloak_api):
    keycloak_settings = settings.auth.model_dump()["keycloak"]
    api_url = keycloak_settings["api_url"]
    realm_name = keycloak_settings["client_id"]
    realm_url = f"{api_url}/realms/{realm_name}"
    well_known_url = f"{realm_url}/.well-known/openid-configuration"
    openid_url = f"{realm_url}/protocol/openid-connect"

    mock_keycloak_api.get(well_known_url).respond(
        json={
            "authorization_endpoint": f"{openid_url}/auth",
            "token_endpoint": f"{openid_url}/token",
            "userinfo_endpoint": f"{openid_url}/userinfo",
            "end_session_endpoint": f"{openid_url}/logout",
            "jwks_uri": f"{openid_url}/certs",
            "issuer": realm_url,
        },
        status_code=200,
        content_type="application/json",
    )


@pytest.fixture
def mock_keycloak_realm(settings, rsa_keys, mock_keycloak_api):
    keycloak_settings = settings.auth.model_dump()["keycloak"]
    api_url = keycloak_settings["api_url"]
    realm_name = keycloak_settings["client_id"]
    realm_url = f"{api_url}/realms/{realm_name}"
    public_pem_str = get_public_key_pem(rsa_keys["public_key"])

    mock_keycloak_api.get(realm_url).respond(
        json={
            "realm": realm_name,
            "public_key": public_pem_str,
            "token-service": f"{realm_url}/protocol/openid-connect/token",
            "account-service": f"{realm_url}/account",
        },
        status_code=200,
        content_type="application/json",
    )


@pytest.fixture
def mock_keycloak_token_refresh(settings, rsa_keys, mock_keycloak_api):
    keycloak_settings = settings.auth.model_dump()["keycloak"]
    api_url = keycloak_settings["api_url"]
    realm_name = keycloak_settings["client_id"]
    realm_url = f"{api_url}/realms/{realm_name}"
    token_url = f"{realm_url}/protocol/openid-connect/token"

    # generate new access and refresh tokens
    expires_in = int(time.time()) + 1000
    private_pem = rsa_keys["private_pem"]
    payload = {
        "sub": "mock_user_id",
        "preferred_username": "mock_username",
        "email": "mock_email@example.com",
        "given_name": "Mock",
        "middle_name": "User",
        "family_name": "Name",
        "exp": expires_in,
    }

    new_access_token = jwt.encode(payload, private_pem, algorithm="RS256")
    new_refresh_token = "mock_new_refresh_token"

    mock_keycloak_api.post(token_url).respond(
        json={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        },
        status_code=200,
        content_type="application/json",
    )


@pytest.fixture
def mock_keycloak_logout(settings, mock_keycloak_api):
    keycloak_settings = settings.auth.model_dump()["keycloak"]
    api_url = keycloak_settings["api_url"]
    realm_name = keycloak_settings["client_id"]
    realm_url = f"{api_url}/realms/{realm_name}"
    logout_url = f"{realm_url}/protocol/openid-connect/logout"

    mock_keycloak_api.post(logout_url).respond(status_code=204)


@pytest.fixture
def mock_keycloak_introspect_token(settings, mock_keycloak_api):
    def _mock_keycloak_introspect_token(user):
        keycloak_settings = settings.auth.model_dump()["keycloak"]
        api_url = keycloak_settings["api_url"]
        realm_name = keycloak_settings["client_id"]
        realm_url = f"{api_url}/realms/{realm_name}"

        payload = {
            "preferred_username": user.username,
            "email": user.email,
            "given_name": user.first_name,
            "middle_name": user.middle_name,
            "family_name": user.last_name,
            "active": user.is_active,
        }
        introspect_url = f"{realm_url}/protocol/openid-connect/token/introspect"

        mock_keycloak_api.post(introspect_url).respond(
            json=payload,
            status_code=200,
            content_type="application/json",
        )

    return _mock_keycloak_introspect_token
