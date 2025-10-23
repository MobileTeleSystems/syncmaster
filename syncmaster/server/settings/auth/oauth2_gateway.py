# SPDX-FileCopyrightText: 2023-2025 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field

from syncmaster.server.settings.auth.keycloak import KeycloakSettings


class OAuth2GatewayProviderSettings(BaseModel):
    """Settings related to Keycloak interaction."""

    keycloak: KeycloakSettings = Field(
        description="Keycloak settings",
    )
