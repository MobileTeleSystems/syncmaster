# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field, model_validator

from syncmaster.schemas.v1.connections.hdfs import (
    HDFSCreateAuthSchema,
    HDFSCreateConnectionSchema,
    HDFSReadAuthSchema,
    HDFSReadConnectionSchema,
    HDFSUpdateAuthSchema,
    HDFSUpdateConnectionSchema,
)
from syncmaster.schemas.v1.connections.hive import (
    CreateHiveAuthSchema,
    CreateHiveConnectionSchema,
    ReadHiveAuthSchema,
    ReadHiveConnectionSchema,
    UpdateHiveAuthSchema,
    UpdateHiveConnectionSchema,
)
from syncmaster.schemas.v1.connections.oracle import (
    CreateOracleAuthSchema,
    CreateOracleConnectionSchema,
    ReadOracleAuthSchema,
    ReadOracleConnectionSchema,
    UpdateOracleAuthSchema,
    UpdateOracleConnectionSchema,
)
from syncmaster.schemas.v1.connections.postgres import (
    CreatePostgresAuthSchema,
    CreatePostgresConnectionSchema,
    ReadPostgresAuthSchema,
    ReadPostgresConnectionSchema,
    UpdatePostgresAuthSchema,
    UpdatePostgresConnectionSchema,
)
from syncmaster.schemas.v1.connections.s3 import (
    S3CreateAuthSchema,
    S3CreateConnectionSchema,
    S3ReadAuthSchema,
    S3ReadConnectionSchema,
    S3UpdateAuthSchema,
    S3UpdateConnectionSchema,
)
from syncmaster.schemas.v1.page import PageSchema
from syncmaster.schemas.v1.types import NameConstr

ReadConnectionDataSchema = (
    ReadHiveConnectionSchema
    | HDFSReadConnectionSchema
    | ReadOracleConnectionSchema
    | ReadPostgresConnectionSchema
    | S3ReadConnectionSchema
)
CreateConnectionDataSchema = (
    CreateHiveConnectionSchema
    | CreateOracleConnectionSchema
    | CreatePostgresConnectionSchema
    | HDFSCreateConnectionSchema
    | S3CreateConnectionSchema
)
UpdateConnectionDataSchema = (
    UpdateHiveConnectionSchema
    | HDFSUpdateConnectionSchema
    | S3UpdateConnectionSchema
    | UpdateOracleConnectionSchema
    | UpdatePostgresConnectionSchema
)
ReadConnectionAuthDataSchema = (
    ReadHiveAuthSchema | ReadOracleAuthSchema | ReadPostgresAuthSchema | S3ReadAuthSchema | HDFSReadAuthSchema
)
CreateConnectionAuthDataSchema = (
    CreateHiveAuthSchema | CreateOracleAuthSchema | CreatePostgresAuthSchema | S3CreateAuthSchema | HDFSCreateAuthSchema
)
UpdateConnectionAuthDataSchema = (
    UpdateHiveAuthSchema | UpdateOracleAuthSchema | UpdatePostgresAuthSchema | S3UpdateAuthSchema | HDFSUpdateAuthSchema
)


class ReadConnectionSchema(BaseModel):
    id: int
    group_id: int
    name: str
    description: str
    auth_data: ReadConnectionAuthDataSchema | None = None
    data: ReadConnectionDataSchema = Field(
        ...,
        discriminator="type",
        alias="connection_data",
    )

    class Config:
        from_attributes = True
        populate_by_name = True


class UpdateConnectionSchema(BaseModel):
    name: NameConstr | None = None  # noqa: F722
    description: str | None = None
    auth_data: UpdateConnectionAuthDataSchema | None = Field(discriminator="type", default=None)
    data: UpdateConnectionDataSchema | None = Field(discriminator="type", alias="connection_data", default=None)

    @model_validator(mode="before")
    def check_types(cls, values):
        data, auth_data = values.get("connection_data"), values.get("auth_data")
        if data and auth_data and data.get("type") != auth_data.get("type"):
            raise ValueError("Connection data and auth data must have same types")
        return values


class CreateConnectionSchema(BaseModel):
    group_id: int = Field(..., description="Connection owner group id")
    name: NameConstr = Field(..., description="Connection name")  # noqa: F722
    description: str = Field(..., description="Additional description")
    data: CreateConnectionDataSchema = Field(
        ...,
        discriminator="type",
        alias="connection_data",
        description=(
            "Data required to connect to the database. These are the parameters that are specified in the "
            "URL request."
        ),
    )
    auth_data: CreateConnectionAuthDataSchema = Field(
        ...,
        discriminator="type",
        description="Credentials for authorization",
    )

    @model_validator(mode="before")
    def check_types(cls, values):
        data, auth_data = values.get("data"), values.get("auth_data")
        if data and auth_data and data.type != auth_data.type:
            raise ValueError("Connection data and auth data must have same types")
        return values


class ConnectionCopySchema(BaseModel):
    new_group_id: int
    new_name: NameConstr | None = None  # noqa: F722
    remove_source: bool = False


class ConnectionPageSchema(PageSchema):
    items: list[ReadConnectionSchema]
