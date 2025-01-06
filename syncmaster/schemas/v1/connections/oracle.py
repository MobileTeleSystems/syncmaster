# SPDX-FileCopyrightText: 2023-2025 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field, model_validator

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.connection_types import ORACLE_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
    UpdateConnectionBaseSchema,
)


class CreateOracleConnectionDataSchema(BaseModel):
    host: str
    port: int
    service_name: str | None = None
    sid: str | None = None
    additional_params: dict = Field(default_factory=dict)

    @model_validator(mode="before")
    def check_owner_id(cls, values):
        sid, service_name = values.get("sid"), values.get("service_name")
        if sid and service_name:
            raise ValueError("You must specify either sid or service_name but not both")
        return values


class ReadOracleConnectionDataSchema(BaseModel):
    host: str
    port: int
    service_name: str | None = None
    sid: str | None = None
    additional_params: dict = Field(default_factory=dict)


class UpdateOracleConnectionDataSchema(BaseModel):
    host: str | None = None
    port: int | None = None
    sid: str | None = None
    service_name: str | None = None
    additional_params: dict | None = Field(default_factory=dict)

    @model_validator(mode="before")
    def check_owner_id(cls, values):
        sid, service_name = values.get("sid"), values.get("service_name")
        if sid and service_name:
            raise ValueError("You must specify either sid or service_name but not both")
        return values


class CreateOracleConnectionSchema(CreateConnectionBaseSchema):
    type: ORACLE_TYPE = Field(..., description="Connection type")
    data: CreateOracleConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the database. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadOracleConnectionSchema(ReadConnectionBaseSchema):
    type: ORACLE_TYPE
    data: ReadOracleConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdateOracleConnectionSchema(UpdateConnectionBaseSchema):
    type: ORACLE_TYPE
    data: UpdateOracleConnectionDataSchema | None = Field(alias="connection_data", default=None)
    auth_data: UpdateBasicAuthSchema | None = None
