# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ConfigDict, Field

from syncmaster.schemas.v1.auth import (
    ReadBasicAuthSchema,
    ReadS3AuthSchema,
    ReadSambaAuthSchema,
)
from syncmaster.schemas.v1.auth.iceberg.basic import (
    ReadIcebergRESTCatalogBasicAuthSchema,
)
from syncmaster.schemas.v1.auth.iceberg.oauth2_client_credentials import (
    ReadIcebergRESTCatalogOAuth2ClientCredentialsAuthSchema,
)
from syncmaster.schemas.v1.types import NameConstr

ReadConnectionAuthDataSchema = (
    ReadBasicAuthSchema
    | ReadS3AuthSchema
    | ReadSambaAuthSchema
    | ReadIcebergRESTCatalogBasicAuthSchema
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
