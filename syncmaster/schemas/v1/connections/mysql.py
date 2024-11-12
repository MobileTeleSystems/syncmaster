# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field, SecretStr

from syncmaster.schemas.v1.connection_types import MYSQL_TYPE


class MySQLBaseSchema(BaseModel):
    type: MYSQL_TYPE

    class Config:
        from_attributes = True


class ReadMySQLConnectionSchema(MySQLBaseSchema):
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class ReadMySQLAuthSchema(MySQLBaseSchema):
    user: str


class UpdateMySQLConnectionSchema(MySQLBaseSchema):
    host: str | None = None
    port: int | None = None
    database_name: str | None = None
    additional_params: dict | None = Field(default_factory=dict)


class UpdateMySQLAuthSchema(MySQLBaseSchema):
    user: str | None = None  # noqa: F722
    password: SecretStr | None = None


class CreateMySQLConnectionSchema(MySQLBaseSchema):
    host: str
    port: int
    database_name: str
    additional_params: dict = Field(default_factory=dict)


class CreateMySQLAuthSchema(MySQLBaseSchema):
    user: str
    password: SecretStr
