# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
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
    UpdateConnectionBaseSchema,
)


class CreateHDFSConnectionDataSchema(BaseModel):
    cluster: str


class ReadHDFSConnectionDataSchema(BaseModel):
    cluster: str


class UpdateHDFSConnectionDataSchema(BaseModel):
    cluster: str


class CreateHDFSConnectionSchema(CreateConnectionBaseSchema):
    type: HDFS_TYPE = Field(..., description="Connection type")
    data: CreateHDFSConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the HDFS cluster. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadHDFSConnectionSchema(ReadConnectionBaseSchema):
    type: HDFS_TYPE
    data: ReadHDFSConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdateHDFSConnectionSchema(UpdateConnectionBaseSchema):
    type: HDFS_TYPE
    data: UpdateHDFSConnectionDataSchema | None = Field(alias="connection_data", default=None)
    auth_data: UpdateBasicAuthSchema | None = None
