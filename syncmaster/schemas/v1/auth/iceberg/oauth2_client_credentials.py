# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field, SecretStr

from syncmaster.schemas.v1.types import URL


class ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema(BaseModel):
    type: Literal["iceberg_rest_oauth2_client_credentials_s3_basic"] = Field(description="Auth type")
    rest_catalog_oauth2_client_id: str
    rest_catalog_oauth2_scopes: list[str] = Field(default_factory=list)
    rest_catalog_oauth2_resource: str | None = None
    rest_catalog_oauth2_audience: str | None = None
    rest_catalog_oauth2_server_uri: URL | None = None
    s3_access_key: str


class CreateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema(
    ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
):
    rest_catalog_oauth2_client_secret: SecretStr
    s3_secret_key: SecretStr


class UpdateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema(
    ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
):
    rest_catalog_oauth2_client_secret: SecretStr | None = None
    s3_secret_key: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("rest_catalog_oauth2_client_secret", "s3_secret_key")
