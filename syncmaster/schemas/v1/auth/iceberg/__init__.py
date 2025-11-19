# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated

from pydantic import Field

from syncmaster.schemas.v1.auth.iceberg.basic import (
    CreateIcebergRESTCatalogBasicAuthSchema,
    ReadIcebergRESTCatalogBasicAuthSchema,
    UpdateIcebergRESTCatalogBasicAuthSchema,
)
from syncmaster.schemas.v1.auth.iceberg.oauth2_client_credentials import (
    CreateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
    ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
    UpdateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
)

CreateIcebergRESTCatalogS3ConnectionAuthDataSchema = Annotated[
    CreateIcebergRESTCatalogBasicAuthSchema | CreateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
    Field(discriminator="type"),
]

ReadIcebergRESTCatalogS3ConnectionAuthDataSchema = Annotated[
    ReadIcebergRESTCatalogBasicAuthSchema | ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
    Field(discriminator="type"),
]

UpdateIcebergRESTCatalogS3ConnectionAuthDataSchema = Annotated[
    UpdateIcebergRESTCatalogBasicAuthSchema | UpdateIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
    Field(discriminator="type"),
]
