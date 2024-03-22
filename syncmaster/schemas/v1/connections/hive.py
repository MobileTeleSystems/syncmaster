# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, SecretStr

from syncmaster.schemas.v1.connection_types import HIVE_TYPE


class HiveBaseSchema(BaseModel):
    type: HIVE_TYPE

    class Config:
        from_attributes = True


class ReadHiveConnectionSchema(HiveBaseSchema):
    cluster: str


class ReadHiveAuthSchema(HiveBaseSchema):
    user: str


class UpdateHiveConnectionSchema(HiveBaseSchema):
    cluster: str | None = None


class UpdateHiveAuthSchema(HiveBaseSchema):
    user: str | None = None
    password: SecretStr | None = None


class CreateHiveConnectionSchema(HiveBaseSchema):
    cluster: str


class CreateHiveAuthSchema(HiveBaseSchema):
    # Needed to create a spark session. For authorization in Kerberos
    user: str
    password: SecretStr
