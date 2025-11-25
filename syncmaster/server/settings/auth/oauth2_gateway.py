# SPDX-FileCopyrightText: 2023-2025 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field

from syncmaster.server.settings.auth.keycloak import KeycloakSettings


class OAuth2GatewayProviderSettings(BaseModel):
    """Settings for OAuth2GatewayProvider.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        auth:
            provider: syncmaster.server.providers.auth.oauth2_gateway_provider.OAuth2GatewayProvider
            keycloak:
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
