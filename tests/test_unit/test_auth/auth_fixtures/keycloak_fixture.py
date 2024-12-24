import json
import time
from base64 import b64encode

import pytest
import pytest_asyncio
import respx
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from itsdangerous import TimestampSigner
from jose import jwt

from syncmaster.server.settings.auth.keycloak import KeycloakSettings


@pytest.fixture(scope="session")
def rsa_keys():
    # create private & public keys to emulate Keycloak signing
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
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
    def _create_session_cookie(user, expire_in_msec=5000) -> str:
        private_pem = rsa_keys["private_pem"]
        session_secret_key = settings.server.session.secret_key

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
    keycloak_settings = KeycloakSettings.model_validate(settings.auth.model_dump()["keycloak"])
    server_url = keycloak_settings.server_url

    async with respx.mock(base_url=server_url, assert_all_called=False) as respx_mock:
        yield respx_mock


@pytest.fixture
def mock_keycloak_well_known(settings, mock_keycloak_api):
    keycloak_settings = KeycloakSettings.model_validate(settings.auth.model_dump()["keycloak"])
    realm_name = keycloak_settings.realm_name

    mock_keycloak_api.get(f"/realms/{realm_name}/.well-known/openid-configuration").respond(
        status_code=200,
        json={
            "authorization_endpoint": f"/realms/{realm_name}/protocol/openid-connect/auth",
            "token_endpoint": f"/realms/{realm_name}/protocol/openid-connect/token",
            "userinfo_endpoint": f"/realms/{realm_name}/protocol/openid-connect/userinfo",
            "end_session_endpoint": f"/realms/{realm_name}/protocol/openid-connect/logout",
            "jwks_uri": f"/realms/{realm_name}/protocol/openid-connect/certs",
            "issuer": f"/realms/{realm_name}",
        },
        content_type="application/json",
    )


@pytest.fixture
def mock_keycloak_realm(settings, rsa_keys, mock_keycloak_api):
    keycloak_settings = KeycloakSettings.model_validate(settings.auth.model_dump()["keycloak"])
    realm_name = keycloak_settings.realm_name
    public_pem_str = get_public_key_pem(rsa_keys["public_key"])

    mock_keycloak_api.get(f"/realms/{realm_name}").respond(
        status_code=200,
        json={
            "realm": realm_name,
            "public_key": public_pem_str,
            "token-service": f"/realms/{realm_name}/protocol/openid-connect/token",
            "account-service": f"/realms/{realm_name}/account",
        },
        content_type="application/json",
    )


@pytest.fixture
def mock_keycloak_token_refresh(settings, rsa_keys, mock_keycloak_api):
    keycloak_settings = KeycloakSettings.model_validate(settings.auth.model_dump()["keycloak"])
    realm_name = keycloak_settings.realm_name

    # generate new access and refresh tokens
    expires_in = int(time.time()) + 5000
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

    mock_keycloak_api.post(f"/realms/{realm_name}/protocol/openid-connect/token").respond(
        status_code=200,
        json={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        },
        content_type="application/json",
    )
