# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field, SecretStr

from app.api.v1.schemas import HIVE_TYPE


class HiveBaseSchema(BaseModel):
    type: HIVE_TYPE


class ReadHiveConnectionSchema(HiveBaseSchema):
    cluster: str
    additional_params: dict = Field(default_factory=dict)


class ReadHiveAuthSchema(HiveBaseSchema):
    user: str


class UpdateHiveConnectionSchema(HiveBaseSchema):
    cluster: str | None
    additional_params: dict | None = Field(default_factory=dict)


class UpdateHiveAuthSchema(HiveBaseSchema):
    pass


class CreateHiveConnectionSchema(HiveBaseSchema):
    additional_params: dict = Field(default_factory=dict)
    cluster: str


class CreateHiveAuthSchema(HiveBaseSchema):
    user: str
    password: SecretStr
