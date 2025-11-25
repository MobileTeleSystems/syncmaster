# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import Field, SecretStr

from syncmaster.schemas.v1.auth.mixins import SecretDumpMixin
from syncmaster.schemas.v1.types import URL


class ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema(SecretDumpMixin):
    type: Literal["iceberg_rest_oauth2_client_credentials"] = Field(description="Auth type")
    rest_catalog_oauth2_client_id: str
    rest_catalog_oauth2_scopes: list[str] = Field(default_factory=list)
    rest_catalog_oauth2_resource: str | None = None
    rest_catalog_oauth2_audience: str | None = None
    rest_catalog_oauth2_token_endpoint: URL | None = None


class CreateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema(
    ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
):
    rest_catalog_oauth2_client_secret: SecretStr


class UpdateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema(
    ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
):
    rest_catalog_oauth2_client_secret: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("rest_catalog_oauth2_client_secret",)
