# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
)
from syncmaster.schemas.v1.auth.basic import UpdateBasicAuthSchema
from syncmaster.schemas.v1.connection_types import FTPS_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class CreateFTPSConnectionDataSchema(BaseModel):
    host: str
    port: int


class ReadFTPSConnectionDataSchema(BaseModel):
    host: str
    port: int


class CreateFTPSConnectionSchema(CreateConnectionBaseSchema):
    type: FTPS_TYPE = Field(..., description="Connection type")
    data: CreateFTPSConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the remote server. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadFTPSConnectionSchema(ReadConnectionBaseSchema):
    type: FTPS_TYPE
    data: ReadFTPSConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdateFTPSConnectionSchema(CreateFTPSConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
