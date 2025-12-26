# SPDX-FileCopyrightText: 2023-present MTS PJSC
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
)


class OracleConnectionDataSchema(BaseModel):
    host: str
    port: int = Field(default=1521, gt=0, le=65535)  # noqa: WPS432
    service_name: str | None = None
    sid: str | None = None
    additional_params: dict = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def validate_connection_identifiers(cls, values):
        sid, service_name = values.get("sid"), values.get("service_name")
        if sid and service_name:
            msg = "You must specify either sid or service_name but not both"
            raise ValueError(msg)
        return values


class CreateOracleConnectionSchema(CreateConnectionBaseSchema):
    type: ORACLE_TYPE = Field(description="Connection type")
    data: OracleConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the database",
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadOracleConnectionSchema(ReadConnectionBaseSchema):
    type: ORACLE_TYPE = Field(description="Connection type")
    data: OracleConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the remote server",
    )
    auth_data: ReadBasicAuthSchema | None = Field(
        default=None,
        description="Credentials for authorization",
    )


class UpdateOracleConnectionSchema(CreateOracleConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
