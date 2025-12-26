# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.connection_types import FTPS_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class FTPSConnectionDataSchema(BaseModel):
    host: str
    port: int = Field(default=21, gt=0, le=65535)


class CreateFTPSConnectionSchema(CreateConnectionBaseSchema):
    type: FTPS_TYPE = Field(description="Connection type")
    data: FTPSConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the remote server",
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadFTPSConnectionSchema(ReadConnectionBaseSchema):
    type: FTPS_TYPE = Field(description="Connection type")
    data: FTPSConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = Field(
        default=None,
        description="Credentials for authorization",
    )


class UpdateFTPSConnectionSchema(CreateFTPSConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
