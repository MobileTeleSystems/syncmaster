# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ConfigDict, Field

from syncmaster.schemas.v1.auth import (
    ReadBasicAuthSchema,
    ReadS3AuthSchema,
    ReadSambaAuthSchema,
)
from syncmaster.schemas.v1.auth.iceberg_rest_s3_delegated import (
    ReadIcebergRESTCatalogBearerAuthSchema,
    ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
)
from syncmaster.schemas.v1.auth.iceberg_rest_s3_direct import (
    ReadIcebergRESTCatalogBearerS3BasicAuthSchema,
    ReadIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema,
)
from syncmaster.schemas.v1.types import NameConstr

ReadConnectionAuthDataSchema = (
    ReadBasicAuthSchema
    | ReadS3AuthSchema
    | ReadSambaAuthSchema
    | ReadIcebergRESTCatalogBearerS3BasicAuthSchema
    | ReadIcebergRESTCatalogOAuth2ClientCredentialsS3BasicAuthSchema
    | ReadIcebergRESTCatalogBearerAuthSchema
    | ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema
)


class CreateConnectionBaseSchema(BaseModel):
    group_id: int = Field(description="Group id the connections is bound to")
    name: NameConstr = Field(description="Connection name")
    description: str = Field(description="Human-readable description")

    model_config = ConfigDict(populate_by_name=True)


class ReadConnectionBaseSchema(CreateConnectionBaseSchema):
    id: int = Field(description="Connection id")

    model_config = ConfigDict(populate_by_name=True)


class ReadAuthDataSchema(BaseModel):
    auth_data: ReadConnectionAuthDataSchema = Field(discriminator="type")
