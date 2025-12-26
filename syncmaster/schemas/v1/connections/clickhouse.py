# SPDX-FileCopyrightText: 2023-present MTS PJSC
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
)


class ClickhouseConnectionDataSchema(BaseModel):
    host: str
    port: int = Field(default=8123, gt=0, le=65535)
    database_name: str | None = None
    additional_params: dict = Field(default_factory=dict)


class CreateClickhouseConnectionSchema(CreateConnectionBaseSchema):
    type: CLICKHOUSE_TYPE = Field(description="Connection type")
    data: ClickhouseConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the database",
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadClickhouseConnectionSchema(ReadConnectionBaseSchema):
    type: CLICKHOUSE_TYPE = Field(description="Connection type")
    data: ClickhouseConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the database",
    )
    auth_data: ReadBasicAuthSchema | None = Field(
        description="Credentials for authorization",
    )


class UpdateClickhouseConnectionSchema(CreateClickhouseConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
