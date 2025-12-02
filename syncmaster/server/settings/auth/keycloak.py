# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import textwrap
from typing import Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    SecretStr,
)


class KeycloakSettings(BaseModel):
    api_url: HttpUrl = Field(description="Keycloak API URL")
    client_id: str = Field(description="Keycloak client ID")
    client_secret: SecretStr = Field(description="Keycloak client secret")
    realm_name: str = Field(description="Keycloak realm name")
    ui_callback_url: str = Field(description="SyncMaster UI auth callback endpoint")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    scope: str = Field(default="openid", description="Keycloak scope")


class KeycloakCookieSettings(BaseModel):
    """Keycloak cookie Middleware Settings.

    See `SessionMiddleware <https://www.starlette.io/middleware/#sessionmiddleware>`_ documentation.

    .. note::

        You can pass here any extra option supported by ``SessionMiddleware``,
        even if it is not mentioned in documentation.

    Examples
    --------

    For development environment:

    .. code-block:: yaml
        :caption: config.yml

        auth:
            provider: syncmaster.server.providers.auth.keycloak_provider.KeycloakAuthProvider
            keycloak: ...
            cookie:
                secret_key: cookie_secret
                name: custom_name
                max_age: null
                same_site: lax
                https_only: false
                domain: localhost

    For production environment:

    .. code-block:: yaml
        :caption: config.yml

        auth:
            provider: syncmaster.server.providers.auth.keycloak_provider.KeycloakAuthProvider
            keycloak: ...
            cookie:
                secret_key: cookie_secret
                name: custom_name
                max_age: 2678400  # 31 days
                same_site: strict
                https_only: true
                domain: example.com

    """

    secret_key: SecretStr = Field(
        description=textwrap.dedent(
            """
            Secret key for encrypting cookies.

            Can be any string. It is recommended to generate random value for every application instance, e.g.:

            .. code:: shell

                pwgen 32 1
            """,
        ),
    )
    name: str = Field(
        default="session",
        description="Name of the session cookie. Change this if there are multiple application under the same domain.",
    )
    max_age: int | None = Field(
        default=14 * 24 * 60 * 60,
        description="Session expiry time in seconds. Defaults to 2 weeks.",
    )
    same_site: Literal["strict", "lax", "none"] = Field(
        default="lax",
        description="Prevents cookie from being sent with cross-site requests.",
    )
    path: str = Field(default="/", description="Path to restrict session cookie access.")
    https_only: bool = Field(default=False, description="Secure flag for HTTPS-only access.")
    domain: str | None = Field(
        default=None,
        description="Domain for sharing cookies between subdomains or cross-domains.",
    )

    model_config = ConfigDict(extra="allow")


class KeycloakAuthProviderSettings(BaseModel):
    """Settings for KeycloakAuthProvider.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        auth:
            provider: syncmaster.server.providers.auth.keycloak_provider.KeycloakAuthProvider
            keycloak:
                api_url: http://localhost:8080/auth
                client_id: my_keycloak_client
                client_secret: keycloak_client_secret
                realm_name: my_realm
                ui_callback_url: http://localhost:8000/auth/realms/my_realm/protocol/openid-connect/auth
                verify_ssl: false
                scope: openid
            cookie:
                secret_key: cookie_secret
    """

    keycloak: KeycloakSettings = Field(
        description="Keycloak settings",
    )
    cookie: KeycloakCookieSettings = Field(
        description="Keycloak cookie settings",
    )
