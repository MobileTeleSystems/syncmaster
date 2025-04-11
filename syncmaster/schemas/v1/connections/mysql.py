# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
)
from syncmaster.schemas.v1.auth.basic import UpdateBasicAuthSchema
from syncmaster.schemas.v1.connection_types import MYSQL_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class CreateMySQLConnectionDataSchema(BaseModel):
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class ReadMySQLConnectionDataSchema(BaseModel):
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class CreateMySQLConnectionSchema(CreateConnectionBaseSchema):
    type: MYSQL_TYPE = Field(description="Connection type")
    data: CreateMySQLConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the database. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadMySQLConnectionSchema(ReadConnectionBaseSchema):
    type: MYSQL_TYPE
    data: ReadMySQLConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdateMySQLConnectionSchema(CreateMySQLConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
