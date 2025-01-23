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
    UpdateConnectionBaseSchema,
)


class CreateSFTPConnectionDataSchema(BaseModel):
    host: str
    port: int


class ReadSFTPConnectionDataSchema(BaseModel):
    host: str
    port: int


class UpdateSFTPConnectionDataSchema(BaseModel):
    host: str | None = None
    port: int | None = None


class CreateSFTPConnectionSchema(CreateConnectionBaseSchema):
    type: SFTP_TYPE = Field(..., description="Connection type")
    data: CreateSFTPConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the remote server. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadSFTPConnectionSchema(ReadConnectionBaseSchema):
    type: SFTP_TYPE
    data: ReadSFTPConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdateSFTPConnectionSchema(UpdateConnectionBaseSchema):
    type: SFTP_TYPE
    data: UpdateSFTPConnectionDataSchema | None = Field(alias="connection_data", default=None)
    auth_data: UpdateBasicAuthSchema | None = None
