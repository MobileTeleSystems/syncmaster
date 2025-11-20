# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from pydantic import Field

from syncmaster.schemas.v1.auth.iceberg_rest_s3_direct.basic import (
    CreateIcebergRESTCatalogBasicS3BasicAuthSchema,
    ReadIcebergRESTCatalogBasicS3BasicAuthSchema,
    UpdateIcebergRESTCatalogBasicS3BasicAuthSchema,
)
from syncmaster.schemas.v1.auth.iceberg_rest_s3_direct.oauth2_client_credentials import (
    CreateIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
    ReadIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
    UpdateIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
)

CreateIcebergRESTCatalogS3DirectConnectionAuthDataSchema = Annotated[
    CreateIcebergRESTCatalogBasicS3BasicAuthSchema | CreateIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
    Field(discriminator="type"),
]

ReadIcebergRESTCatalogS3DirectConnectionAuthDataSchema = Annotated[
    ReadIcebergRESTCatalogBasicS3BasicAuthSchema | ReadIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
    Field(discriminator="type"),
]

UpdateIcebergRESTCatalogS3DirectConnectionAuthDataSchema = Annotated[
    UpdateIcebergRESTCatalogBasicS3BasicAuthSchema | UpdateIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
    Field(discriminator="type"),
]
