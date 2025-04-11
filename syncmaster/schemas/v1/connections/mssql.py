# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
)
from syncmaster.schemas.v1.auth.basic import UpdateBasicAuthSchema
from syncmaster.schemas.v1.connection_types import MSSQL_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class CreateMSSQLConnectionDataSchema(BaseModel):
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class ReadMSSQLConnectionDataSchema(BaseModel):
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class CreateMSSQLConnectionSchema(CreateConnectionBaseSchema):
    type: MSSQL_TYPE = Field(description="Connection type")
    data: CreateMSSQLConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the database. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadMSSQLConnectionSchema(ReadConnectionBaseSchema):
    type: MSSQL_TYPE
    data: ReadMSSQLConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdateMSSQLConnectionSchema(CreateMSSQLConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
