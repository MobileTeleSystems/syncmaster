import json
from base64 import b64encode

import responses
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat
from itsdangerous import TimestampSigner
from jose import jwt

# copied from .env.docker as backend tries to send requests to corresponding
KEYCLOAK_CONFIG = {
    "server_url": "http://keycloak:8080",
    "realm_name": "manually_created",
    "redirect_uri": "http://localhost:8000/v1/auth/callback",
    "client_secret": "generated_by_keycloak",
    "scope": "email",
    "client_id": "test-client",
}
# create private & public keys to emulate Keycloak signing
PRIVATE_KEY = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)
PRIVATE_PEM = PRIVATE_KEY.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)
PUBLIC_KEY = PRIVATE_KEY.public_key()


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


def create_session_cookie(payload: dict, session_secret_key: str) -> str:
    access_token = jwt.encode(payload, PRIVATE_PEM, algorithm="RS256")
    refresh_token = "mock_refresh_token"
    session_data = {
        "access_token": access_token,
        "refresh_token": refresh_token,
    }

    signer = TimestampSigner(session_secret_key)
    json_bytes = json.dumps(session_data).encode("utf-8")
    base64_bytes = b64encode(json_bytes)
    signed_data = signer.sign(base64_bytes)
    return signed_data.decode("utf-8")


def mock_keycloak_well_known(responses_mock):
    server_url = KEYCLOAK_CONFIG.get("server_url")
    realm_name = KEYCLOAK_CONFIG.get("realm_name")
    well_known_url = f"{server_url}/realms/{realm_name}/.well-known/openid-configuration"

    responses_mock.add(
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


def mock_keycloak_token_endpoint(responses_mock, access_token: str, refresh_token: str):
    server_url = KEYCLOAK_CONFIG.get("server_url")
    realm_name = KEYCLOAK_CONFIG.get("realm_name")
    token_url = f"{server_url}/realms/{realm_name}/protocol/openid-connect/token"

    responses_mock.add(
        responses.POST,
        token_url,
        body=json.dumps(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": 3600,
            },
        ),
        status=200,
        content_type="application/json",
    )


def mock_keycloak_realm(responses_mock):
    server_url = KEYCLOAK_CONFIG.get("server_url")
    realm_name = KEYCLOAK_CONFIG.get("realm_name")
    realm_url = f"{server_url}/realms/{realm_name}"

    responses_mock.add(
        responses.GET,
        realm_url,
        json={
            "realm": realm_name,
            "public_key": get_public_key_pem(PUBLIC_KEY),
            "token-service": f"{server_url}/realms/{realm_name}/protocol/openid-connect/token",
            "account-service": f"{server_url}/realms/{realm_name}/account",
        },
        status=200,
        content_type="application/json",
    )
