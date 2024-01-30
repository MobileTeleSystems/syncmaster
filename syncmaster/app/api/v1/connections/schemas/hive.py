# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, SecretStr

from app.api.v1.schemas import HIVE_TYPE


class HiveBaseSchema(BaseModel):
    type: HIVE_TYPE


class ReadHiveConnectionSchema(HiveBaseSchema):
    cluster: str


class ReadHiveAuthSchema(HiveBaseSchema):
    user: str


class UpdateHiveConnectionSchema(HiveBaseSchema):
    cluster: str | None


class UpdateHiveAuthSchema(HiveBaseSchema):
    pass


class CreateHiveConnectionSchema(HiveBaseSchema):
    cluster: str


class CreateHiveAuthSchema(HiveBaseSchema):
    user: str
    password: SecretStr
