# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field, SecretStr


class KeycloakSettings(BaseModel):

    server_url: str = Field(description="Keycloak server URL")
    client_id: str = Field(description="Keycloak client ID")
    client_secret: SecretStr = Field(description="Keycloak client secret")
    realm_name: str = Field(description="Keycloak realm name")
    redirect_uri: str = Field(description="Redirect URI")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    scope: str = Field(default="openid", description="Keycloak scope")


class KeycloakAuthProviderSettings(BaseModel):
    """Settings for KeycloakAuthProvider.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        auth:
            provider: syncmaster.server.providers.auth.keycloak_provider.KeycloakAuthProvider
            server_url: http://localhost:8080/auth
            client_id: my_keycloak_client
            client_secret: keycloak_client_secret
            realm_name: my_realm
            redirect_uri: http://localhost:8000/auth/realms/my_realm/protocol/openid-connect/auth
            verify_ssl: false
            scope: openid
    """

    keycloak: KeycloakSettings = Field(
        description="Keycloak settings",
    )
