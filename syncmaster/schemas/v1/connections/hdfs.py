# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, SecretStr

from syncmaster.schemas.v1.connection_types import HDFS_TYPE


class HDFSConnectionBaseSchema(BaseModel):
    type: HDFS_TYPE

    class Config:
        from_attributes = True


class HDFSReadConnectionSchema(HDFSConnectionBaseSchema):
    cluster: str


class HDFSCreateConnectionSchema(HDFSConnectionBaseSchema):
    cluster: str


class HDFSUpdateConnectionSchema(HDFSConnectionBaseSchema):
    cluster: str


class HDFSReadAuthSchema(HDFSConnectionBaseSchema):
    user: str


class HDFSCreateAuthSchema(HDFSConnectionBaseSchema):
    # Needed to create a spark session. For authorization in Kerberos
    user: str
    password: SecretStr


class HDFSUpdateAuthSchema(HDFSConnectionBaseSchema):
    user: str | None = None
    password: SecretStr | None = None
