# SPDX-FileCopyrightText: 2023-2025 MTS PJSC
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
    UpdateConnectionBaseSchema,
)


class CreateHiveConnectionDataSchema(BaseModel):
    cluster: str


class ReadHiveConnectionDataSchema(BaseModel):
    cluster: str


class UpdateHiveConnectionDataSchema(BaseModel):
    cluster: str | None = None


class CreateHiveConnectionSchema(CreateConnectionBaseSchema):
    type: HIVE_TYPE = Field(..., description="Connection type")
    data: CreateHiveConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the database. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadHiveConnectionSchema(ReadConnectionBaseSchema):
    type: HIVE_TYPE
    data: ReadHiveConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdateHiveConnectionSchema(UpdateConnectionBaseSchema):
    type: HIVE_TYPE
    data: UpdateHiveConnectionDataSchema | None = Field(alias="connection_data", default=None)
    auth_data: UpdateBasicAuthSchema | None = None
