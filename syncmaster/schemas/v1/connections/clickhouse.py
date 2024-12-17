# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.connection_types import CLICKHOUSE_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
    UpdateConnectionBaseSchema,
)


class CreateClickhouseConnectionDataSchema(BaseModel):
    host: str
    port: int
    database_name: str | None = None
    additional_params: dict = Field(default_factory=dict)


class ReadClickhouseConnectionDataSchema(BaseModel):
    host: str
    port: int
    database_name: str | None = None
    additional_params: dict = Field(default_factory=dict)


class UpdateClickhouseConnectionDataSchema(BaseModel):
    host: str | None = None
    port: int | None = None
    database_name: str | None = None
    additional_params: dict | None = Field(default_factory=dict)


class CreateClickhouseConnectionSchema(CreateConnectionBaseSchema):
    type: CLICKHOUSE_TYPE = Field(..., description="Connection type")
    data: CreateClickhouseConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the database. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadClickhouseConnectionSchema(ReadConnectionBaseSchema):
    type: CLICKHOUSE_TYPE
    data: ReadClickhouseConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdateClickhouseConnectionSchema(UpdateConnectionBaseSchema):
    type: CLICKHOUSE_TYPE
    data: UpdateClickhouseConnectionDataSchema | None = Field(alias="connection_data", default=None)
    auth_data: UpdateBasicAuthSchema | None = None
