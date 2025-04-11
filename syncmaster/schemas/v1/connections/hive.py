# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
)
from syncmaster.schemas.v1.auth.basic import UpdateBasicAuthSchema
from syncmaster.schemas.v1.connection_types import HIVE_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class CreateHiveConnectionDataSchema(BaseModel):
    cluster: str


class ReadHiveConnectionDataSchema(BaseModel):
    cluster: str


class CreateHiveConnectionSchema(CreateConnectionBaseSchema):
    type: HIVE_TYPE = Field(description="Connection type")
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


class UpdateHiveConnectionSchema(CreateHiveConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
