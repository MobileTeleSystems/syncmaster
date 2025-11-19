# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth.basic import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.connection_types import SFTP_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class SFTPConnectionDataSchema(BaseModel):
    host: str
    port: int = Field(default=22, gt=0, le=65535)  # noqa: WPS432


class CreateSFTPConnectionSchema(CreateConnectionBaseSchema):
    type: SFTP_TYPE = Field(description="Connection type")
    data: SFTPConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the remote server",
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadSFTPConnectionSchema(ReadConnectionBaseSchema):
    type: SFTP_TYPE = Field(description="Connection type")
    data: SFTPConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the remote server",
    )
    auth_data: ReadBasicAuthSchema | None = Field(
        default=None,
        description="Credentials for authorization",
    )


class UpdateSFTPConnectionSchema(CreateSFTPConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
