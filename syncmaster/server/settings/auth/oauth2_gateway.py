# SPDX-FileCopyrightText: 2025-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field, HttpUrl, SecretStr


class OAuth2GatewayKeycloakSettings(BaseModel):
    api_url: HttpUrl = Field(description="Keycloak API URL")
    client_id: str = Field(description="Keycloak client ID")
    client_secret: SecretStr = Field(description="Keycloak client secret")
    realm_name: str = Field(description="Keycloak realm name")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")


class OAuth2GatewayProviderSettings(BaseModel):
    """Settings for OAuth2GatewayProvider.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        auth:
            provider: syncmaster.server.providers.auth.oauth2_gateway_provider.OAuth2GatewayProvider
            keycloak:
                api_url: http://localhost:8080/auth
                client_id: my_keycloak_client
                client_secret: keycloak_client_secret
                realm_name: my_realm
                verify_ssl: false
    """

    keycloak: OAuth2GatewayKeycloakSettings = Field(
        description="Keycloak settings",
    )
