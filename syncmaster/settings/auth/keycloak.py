# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import AnyHttpUrl, BaseModel, Field, SecretStr

from syncmaster.settings.auth.jwt import JWTSettings


class KeycloakSettings(BaseModel):
    """Settings related to Keycloak interaction."""

    server_url: AnyHttpUrl = Field(
        default="https://isso.mts.ru/auth/",
        description="Keycloak server URL.",
    )
    realm_name: str = Field(
        default="mts",
        description="Keycloak realm name.",
    )
    client_id: str = Field(
        default="syncmaster_dev",
        description="Keycloak client ID.",
    )
    client_secret: SecretStr = Field(
        "VoLrqGz1HGjp6MiwzRaGWIu7z7imKIHb",
        description="Keycloak client secret.",
    )
    redirect_uri: AnyHttpUrl = Field(
        "/",
        description="Redirect URI for authentication.",
    )
    access_token: JWTSettings = Field(description="Access-token related settings")
    # scope: str = Field(
    #     default="email",
    #     description="Scopes for authentication, separated by spaces.",
    # )
    # introspection_delay: int = Field(
    #     default=60,
    #     description="Delay in seconds between token introspections.",
    # )
    # token_url: AnyHttpUrl = Field(
    #     ...,  # Required field
    #     description="Token URL for Keycloak.",
    # )
