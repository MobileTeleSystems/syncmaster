# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field, SecretStr, model_validator

from syncmaster.schemas.v1.connection_types import ORACLE_TYPE
from syncmaster.schemas.v1.types import NameConstr


class OracleBaseSchema(BaseModel):
    type: ORACLE_TYPE

    class Config:
        from_attributes = True


class ReadOracleConnectionSchema(OracleBaseSchema):
    host: str
    port: int
    service_name: str | None = None
    sid: str | None = None
    additional_params: dict = Field(default_factory=dict)


class ReadOracleAuthSchema(OracleBaseSchema):
    user: str


class UpdateOracleConnectionSchema(OracleBaseSchema):
    host: str | None = None
    sid: str | None = None
    service_name: str | None = None
    additional_params: dict | None = Field(default_factory=dict)


class UpdateOracleAuthSchema(OracleBaseSchema):
    user: NameConstr | None = None  # noqa: F722
    password: SecretStr | None = None


class CreateOracleConnectionSchema(OracleBaseSchema):
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


class CreateOracleAuthSchema(OracleBaseSchema):
    user: str
    password: SecretStr
