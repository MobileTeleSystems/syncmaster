# SPDX-FileCopyrightText: 2023-2025 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.connection_types import POSTGRES_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
    UpdateConnectionBaseSchema,
)


class CreatePostgresConnectionDataSchema(BaseModel):
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class ReadPostgresConnectionDataSchema(BaseModel):
    host: str
    port: int = Field(gt=0, le=65535)
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class UpdatePostgresConnectionDataSchema(BaseModel):
    host: str | None = None
    port: int | None = None
    database_name: str | None = None
    additional_params: dict | None = Field(default_factory=dict)


class CreatePostgresConnectionSchema(CreateConnectionBaseSchema):
    type: POSTGRES_TYPE = Field(..., description="Connection type")
    data: CreatePostgresConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the database. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadPostgresConnectionSchema(ReadConnectionBaseSchema):
    type: POSTGRES_TYPE
    data: ReadPostgresConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdatePostgresConnectionSchema(UpdateConnectionBaseSchema):
    type: POSTGRES_TYPE
    data: UpdatePostgresConnectionDataSchema | None = Field(alias="connection_data", default=None)
    auth_data: UpdateBasicAuthSchema | None = None
