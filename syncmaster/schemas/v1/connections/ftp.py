# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
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
    UpdateConnectionBaseSchema,
)


class CreateFTPConnectionDataSchema(BaseModel):
    host: str
    port: int


class ReadFTPConnectionDataSchema(BaseModel):
    host: str
    port: int


class UpdateFTPConnectionDataSchema(BaseModel):
    host: str | None = None
    port: int | None = None


class CreateFTPConnectionSchema(CreateConnectionBaseSchema):
    type: FTP_TYPE = Field(..., description="Connection type")
    data: CreateFTPConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the remote server. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadFTPConnectionSchema(ReadConnectionBaseSchema):
    type: FTP_TYPE
    data: ReadFTPConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdateFTPConnectionSchema(UpdateConnectionBaseSchema):
    type: FTP_TYPE
    data: UpdateFTPConnectionDataSchema | None = Field(alias="connection_data", default=None)
    auth_data: UpdateBasicAuthSchema | None = None
