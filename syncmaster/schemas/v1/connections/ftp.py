# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.connection_types import FTP_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class FTPConnectionDataSchema(BaseModel):
    host: str
    port: int = Field(default=21, gt=0, le=65535)


class CreateFTPConnectionSchema(CreateConnectionBaseSchema):
    type: FTP_TYPE = Field(description="Connection type")
    data: FTPConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the remote server",
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadFTPConnectionSchema(ReadConnectionBaseSchema):
    type: FTP_TYPE = Field(description="Connection type")
    data: FTPConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the remote server",
    )
    auth_data: ReadBasicAuthSchema | None = Field(
        default=None,
        description="Credentials for authorization",
    )


class UpdateFTPConnectionSchema(CreateFTPConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
