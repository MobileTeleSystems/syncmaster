# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field, SecretStr

from syncmaster.schemas.v1.connection_types import MSSQL_TYPE


class MSSQLBaseSchema(BaseModel):
    type: MSSQL_TYPE

    class Config:
        from_attributes = True


class ReadMSSQLConnectionSchema(MSSQLBaseSchema):
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class ReadMSSQLAuthSchema(MSSQLBaseSchema):
    user: str


class UpdateMSSQLConnectionSchema(MSSQLBaseSchema):
    host: str | None = None
    port: int | None = None
    database_name: str | None = None
    additional_params: dict | None = Field(default_factory=dict)


class UpdateMSSQLAuthSchema(MSSQLBaseSchema):
    user: str | None = None  # noqa: F722
    password: SecretStr | None = None


class CreateMSSQLConnectionSchema(MSSQLBaseSchema):
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class CreateMSSQLAuthSchema(MSSQLBaseSchema):
    user: str
    password: SecretStr
