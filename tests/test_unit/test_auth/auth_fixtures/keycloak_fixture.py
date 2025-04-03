import json
import time
from base64 import b64encode

import jwt
import pytest
import responses
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from itsdangerous import TimestampSigner


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
    def _create_session_cookie(user, expire_in_msec=60000) -> str:
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


@pytest.fixture
def mock_keycloak_well_known(settings):
    keycloak_settings = settings.auth.model_dump()["keycloak"]
    server_url = keycloak_settings["server_url"]
    realm_name = keycloak_settings["client_id"]
    well_known_url = f"{server_url}/realms/{realm_name}/.well-known/openid-configuration"

    responses.add(
        responses.GET,
        well_known_url,
        json={
            "authorization_endpoint": f"{server_url}/realms/{realm_name}/protocol/openid-connect/auth",
            "token_endpoint": f"{server_url}/realms/{realm_name}/protocol/openid-connect/token",
            "userinfo_endpoint": f"{server_url}/realms/{realm_name}/protocol/openid-connect/userinfo",
            "end_session_endpoint": f"{server_url}/realms/{realm_name}/protocol/openid-connect/logout",
            "jwks_uri": f"{server_url}/realms/{realm_name}/protocol/openid-connect/certs",
            "issuer": f"{server_url}/realms/{realm_name}",
        },
        status=200,
        content_type="application/json",
    )


@pytest.fixture
def mock_keycloak_realm(settings, rsa_keys):
    keycloak_settings = settings.auth.model_dump()["keycloak"]
    server_url = keycloak_settings["server_url"]
    realm_name = keycloak_settings["client_id"]
    realm_url = f"{server_url}/realms/{realm_name}"
    public_pem_str = get_public_key_pem(rsa_keys["public_key"])

    responses.add(
        responses.GET,
        realm_url,
        json={
            "realm": realm_name,
            "public_key": public_pem_str,
            "token-service": f"{server_url}/realms/{realm_name}/protocol/openid-connect/token",
            "account-service": f"{server_url}/realms/{realm_name}/account",
        },
        status=200,
        content_type="application/json",
    )


@pytest.fixture
def mock_keycloak_token_refresh(settings, rsa_keys):
    keycloak_settings = settings.auth.model_dump()["keycloak"]
    server_url = keycloak_settings["server_url"]
    realm_name = keycloak_settings["client_id"]
    token_url = f"{server_url}/realms/{realm_name}/protocol/openid-connect/token"

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

    responses.add(
        responses.POST,
        token_url,
        json={
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer",
            "expires_in": expires_in,
        },
        status=200,
        content_type="application/json",
    )
