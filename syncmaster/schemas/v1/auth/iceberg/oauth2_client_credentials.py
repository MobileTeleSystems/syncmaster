# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class IcebergRESTCatalogOAuth2ClientCredentialsAuthSchema(BaseModel):
    type: Literal["iceberg_rest_oauth2_client_credentials_s3_basic"]


class CreateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema(IcebergRESTCatalogOAuth2ClientCredentialsAuthSchema):
    metastore_oauth2_client_id: str
    metastore_oauth2_client_secret: SecretStr
    metastore_oauth2_scopes: list[str] = Field(default_factory=list)
    metastore_oauth2_resource: str | None = None
    metastore_oauth2_audience: str | None = None
    metastore_oauth2_server_uri: str | None = None
    s3_access_key: str
    s3_secret_key: SecretStr


class ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema(IcebergRESTCatalogOAuth2ClientCredentialsAuthSchema):
    metastore_oauth2_client_id: str
    metastore_oauth2_scopes: list[str]
    metastore_oauth2_resource: str | None
    metastore_oauth2_audience: str | None
    metastore_oauth2_server_uri: str | None
    s3_access_key: str


class UpdateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema(
    CreateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
):
    metastore_oauth2_client_secret: SecretStr | None = None
    s3_secret_key: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("metastore_oauth2_client_secret", "s3_secret_key")
