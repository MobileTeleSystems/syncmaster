# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.connection_types import HDFS_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class HDFSConnectionDataSchema(BaseModel):
    cluster: str


class CreateHDFSConnectionSchema(CreateConnectionBaseSchema):
    type: HDFS_TYPE = Field(description="Connection type")
    data: HDFSConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the HDFS cluster",
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadHDFSConnectionSchema(ReadConnectionBaseSchema):
    type: HDFS_TYPE = Field(description="Connection type")
    data: HDFSConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the HDFS cluster",
    )
    auth_data: ReadBasicAuthSchema | None = Field(
        default=None,
        description="Credentials for authorization",
    )


class UpdateHDFSConnectionSchema(CreateHDFSConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
