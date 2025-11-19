# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth.iceberg import (
    CreateIcebergRESTCatalogS3ConnectionAuthDataSchema,
    ReadIcebergRESTCatalogS3ConnectionAuthDataSchema,
    UpdateIcebergRESTCatalogS3ConnectionAuthDataSchema,
)
from syncmaster.schemas.v1.connection_types import ICEBERG_REST_S3_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)
from syncmaster.schemas.v1.types import URL


class IcebergRESTCatalogS3ConnectionDataSchema(BaseModel):
    metastore_url: URL
    s3_warehouse_path: str
    s3_host: str
    s3_port: int | None = Field(default=None, gt=0, le=65535)  # noqa: WPS432
    s3_protocol: Literal["http", "https"] = "https"
    s3_bucket: str
    s3_region: str
    s3_bucket_style: Literal["domain", "path"] = "path"
    s3_additional_params: dict = Field(default_factory=dict)


class CreateIcebergConnectionSchema(CreateConnectionBaseSchema):
    type: ICEBERG_REST_S3_TYPE = Field(description="Connection type")
    data: IcebergRESTCatalogS3ConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to REST catalog and to object storage",
    )
    auth_data: CreateIcebergRESTCatalogS3ConnectionAuthDataSchema = Field(
        description="Credentials for REST Catalog and object storage",
    )


class ReadIcebergConnectionSchema(ReadConnectionBaseSchema):
    type: ICEBERG_REST_S3_TYPE = Field(description="Connection type")
    data: IcebergRESTCatalogS3ConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to REST catalog and to object storage",
    )
    auth_data: ReadIcebergRESTCatalogS3ConnectionAuthDataSchema | None = None


class UpdateIcebergConnectionSchema(CreateIcebergConnectionSchema):
    auth_data: UpdateIcebergRESTCatalogS3ConnectionAuthDataSchema = Field(
        description="Credentials for REST Catalog and object storage",
    )
