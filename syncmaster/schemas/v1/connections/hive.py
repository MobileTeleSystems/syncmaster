# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.connection_types import HIVE_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class HiveConnectionDataSchema(BaseModel):
    cluster: str


class CreateHiveConnectionSchema(CreateConnectionBaseSchema):
    type: HIVE_TYPE = Field(description="Connection type")
    data: HiveConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the database",
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadHiveConnectionSchema(ReadConnectionBaseSchema):
    type: HIVE_TYPE = Field(description="Connection type")
    data: HiveConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the remote server",
    )
    auth_data: ReadBasicAuthSchema | None = Field(
        default=None,
        description="Credentials for authorization",
    )


class UpdateHiveConnectionSchema(CreateHiveConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
