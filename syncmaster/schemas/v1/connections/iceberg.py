# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth.iceberg_rest_basic import (
    CreateIcebergRESTCatalogBasicAuthSchema,
    ReadIcebergRESTCatalogBasicAuthSchema,
    UpdateIcebergRESTCatalogBasicAuthSchema,
)
from syncmaster.schemas.v1.connection_types import ICEBERG_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class CreateIcebergRESTCatalogS3ConnectionDataSchema(BaseModel):
    metastore_url: str
    s3_warehouse_path: str
    s3_host: str
    s3_port: int | None = None
    s3_protocol: Literal["http", "https"] = "https"
    s3_bucket: str
    s3_region: str
    s3_path_style_access: bool = False


class ReadIcebergRESTCatalogS3ConnectionDataSchema(BaseModel):
    metastore_url: str
    s3_warehouse_path: str
    s3_host: str
    s3_port: int | None = None
    s3_protocol: Literal["http", "https"] = "https"
    s3_bucket: str
    s3_region: str
    s3_path_style_access: bool = False


class CreateIcebergConnectionSchema(CreateConnectionBaseSchema):
    type: ICEBERG_TYPE = Field(description="Connection type")
    data: CreateIcebergRESTCatalogS3ConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the database. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateIcebergRESTCatalogBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadIcebergConnectionSchema(ReadConnectionBaseSchema):
    type: ICEBERG_TYPE
    data: ReadIcebergRESTCatalogS3ConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadIcebergRESTCatalogBasicAuthSchema | None = None


class UpdateIcebergConnectionSchema(CreateIcebergConnectionSchema):
    auth_data: UpdateIcebergRESTCatalogBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
