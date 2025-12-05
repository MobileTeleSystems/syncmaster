# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from pydantic import Field

from syncmaster.schemas.v1.auth.iceberg_rest_s3_direct.bearer import (
    CreateIcebergRESTCatalogBearerS3BasicAuthSchema,
    ReadIcebergRESTCatalogBearerS3BasicAuthSchema,
    UpdateIcebergRESTCatalogBearerS3BasicAuthSchema,
)
from syncmaster.schemas.v1.auth.iceberg_rest_s3_direct.oauth2_client_credentials import (
    CreateIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
    ReadIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
    UpdateIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
)

CreateIcebergRESTCatalogS3DirectConnectionAuthDataSchema = Annotated[
    CreateIcebergRESTCatalogBearerS3BasicAuthSchema | CreateIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
    Field(discriminator="type"),
]

ReadIcebergRESTCatalogS3DirectConnectionAuthDataSchema = Annotated[
    ReadIcebergRESTCatalogBearerS3BasicAuthSchema | ReadIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
    Field(discriminator="type"),
]

UpdateIcebergRESTCatalogS3DirectConnectionAuthDataSchema = Annotated[
    UpdateIcebergRESTCatalogBearerS3BasicAuthSchema | UpdateIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
    Field(discriminator="type"),
]
