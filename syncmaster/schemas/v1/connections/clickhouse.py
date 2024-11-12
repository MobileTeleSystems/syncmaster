# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field, SecretStr

from syncmaster.schemas.v1.connection_types import CLICKHOUSE_TYPE


class ClickhouseBaseSchema(BaseModel):
    type: CLICKHOUSE_TYPE

    class Config:
        from_attributes = True


class ReadClickhouseConnectionSchema(ClickhouseBaseSchema):
    host: str
    port: int
    database: str | None = None
    additional_params: dict = Field(default_factory=dict)


class ReadClickhouseAuthSchema(ClickhouseBaseSchema):
    user: str


class UpdateClickhouseConnectionSchema(ClickhouseBaseSchema):
    host: str | None = None
    port: int | None = None
    database: str | None = None
    additional_params: dict | None = Field(default_factory=dict)


class UpdateClickhouseAuthSchema(ClickhouseBaseSchema):
    user: str | None = None  # noqa: F722
    password: SecretStr | None = None


class CreateClickhouseConnectionSchema(ClickhouseBaseSchema):
    host: str
    port: int
    database: str | None = None
    additional_params: dict = Field(default_factory=dict)


class CreateClickhouseAuthSchema(ClickhouseBaseSchema):
    user: str
    password: SecretStr
