# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from syncmaster.schemas.v1.auth.iceberg_rest_s3_delegated import (
    CreateIcebergRESTCatalogS3DelegatedConnectionAuthDataSchema,
    ReadIcebergRESTCatalogS3DelegatedConnectionAuthDataSchema,
    UpdateIcebergRESTCatalogS3DelegatedConnectionAuthDataSchema,
)
from syncmaster.schemas.v1.auth.iceberg_rest_s3_direct import (
    CreateIcebergRESTCatalogS3DirectConnectionAuthDataSchema,
    ReadIcebergRESTCatalogS3DirectConnectionAuthDataSchema,
    UpdateIcebergRESTCatalogS3DirectConnectionAuthDataSchema,
)
from syncmaster.schemas.v1.connection_types import ICEBERG_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)
from syncmaster.schemas.v1.types import URL


class IcebergRESTCatalogS3DirectConnectionDataSchema(BaseModel):
    type: Literal["iceberg_rest_s3_direct"]
    rest_catalog_url: URL
    s3_warehouse_path: str
    s3_host: str
    s3_port: int | None = Field(default=None, gt=0, le=65535)
    s3_protocol: Literal["http", "https"] = "https"
    s3_bucket: str
    s3_region: str
    s3_bucket_style: Literal["domain", "path"] = "path"
    s3_additional_params: dict = Field(default_factory=dict)


class IcebergRESTCatalogS3DelegatedConnectionDataSchema(BaseModel):
    type: Literal["iceberg_rest_s3_delegated"]
    rest_catalog_url: URL
    s3_warehouse_name: str | None = None
    s3_access_delegation: Literal["vended-credentials", "remote-signing"] = "vended-credentials"


IcebergConnectionDataSchema = Annotated[
    IcebergRESTCatalogS3DirectConnectionDataSchema | IcebergRESTCatalogS3DelegatedConnectionDataSchema,
    Field(discriminator="type"),
]

CreateIcebergAuthDataSchema = Annotated[
    CreateIcebergRESTCatalogS3DirectConnectionAuthDataSchema
    | CreateIcebergRESTCatalogS3DelegatedConnectionAuthDataSchema,
    Field(discriminator="type"),
]

ReadIcebergAuthDataSchema = Annotated[
    ReadIcebergRESTCatalogS3DirectConnectionAuthDataSchema | ReadIcebergRESTCatalogS3DelegatedConnectionAuthDataSchema,
    Field(discriminator="type"),
]

UpdateIcebergAuthDataSchema = Annotated[
    UpdateIcebergRESTCatalogS3DirectConnectionAuthDataSchema
    | UpdateIcebergRESTCatalogS3DelegatedConnectionAuthDataSchema,
    Field(discriminator="type"),
]


class CreateIcebergConnectionSchema(CreateConnectionBaseSchema):
    type: ICEBERG_TYPE = Field(description="Connection type")
    data: IcebergConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to REST catalog and to object storage",
    )
    auth_data: CreateIcebergAuthDataSchema = Field(
        description="Credentials for REST Catalog and object storage",
    )

    @model_validator(mode="after")
    def connection_and_auth_data_match(self):
        if not self.auth_data:
            return self
        if self.data.type == "iceberg_rest_s3_direct" and "s3" not in self.auth_data.type:
            msg = "Cannot create direct S3 connection without S3 credentials"
            raise ValueError(msg)
        if self.data.type == "iceberg_rest_s3_delegated" and "s3" in self.auth_data.type:
            msg = "Cannot create delegated S3 connection with S3 credentials"
            raise ValueError(msg)
        return self


class ReadIcebergConnectionSchema(ReadConnectionBaseSchema):
    type: ICEBERG_TYPE = Field(description="Connection type")
    data: IcebergConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to REST catalog and to object storage",
    )
    auth_data: ReadIcebergAuthDataSchema | None = Field(
        default=None,
        description="Credentials for REST Catalog and object storage",
    )


class UpdateIcebergConnectionSchema(CreateIcebergConnectionSchema):
    auth_data: UpdateIcebergAuthDataSchema = Field(
        description="Credentials for REST Catalog and object storage",
    )
