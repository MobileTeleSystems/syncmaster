# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from pydantic import Field

from syncmaster.schemas.v1.auth.iceberg_rest_s3_delegated.bearer import (
    CreateIcebergRESTCatalogBearerAuthSchema,
    ReadIcebergRESTCatalogBearerAuthSchema,
    UpdateIcebergRESTCatalogBearerAuthSchema,
)
from syncmaster.schemas.v1.auth.iceberg_rest_s3_delegated.oauth2_client_credentials import (
    CreateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
    ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
    UpdateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
)

CreateIcebergRESTCatalogS3DelegatedConnectionAuthDataSchema = Annotated[
    CreateIcebergRESTCatalogBearerAuthSchema | CreateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
    Field(discriminator="type"),
]

ReadIcebergRESTCatalogS3DelegatedConnectionAuthDataSchema = Annotated[
    ReadIcebergRESTCatalogBearerAuthSchema | ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
    Field(discriminator="type"),
]

UpdateIcebergRESTCatalogS3DelegatedConnectionAuthDataSchema = Annotated[
    UpdateIcebergRESTCatalogBearerAuthSchema | UpdateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
    Field(discriminator="type"),
]
