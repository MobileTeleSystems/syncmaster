# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateSambaAuthSchema,
    ReadSambaAuthSchema,
)
from syncmaster.schemas.v1.auth.samba import UpdateSambaAuthSchema
from syncmaster.schemas.v1.connection_types import SAMBA_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class CreateSambaConnectionDataSchema(BaseModel):
    host: str
    share: str
    port: int | None = None
    protocol: Literal["SMB", "NetBIOS"] = "SMB"
    domain: str = ""


class ReadSambaConnectionDataSchema(BaseModel):
    host: str
    share: str
    port: int | None
    protocol: Literal["SMB", "NetBIOS"]
    domain: str


class CreateSambaConnectionSchema(CreateConnectionBaseSchema):
    type: SAMBA_TYPE = Field(description="Connection type")
    data: CreateSambaConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the remote server. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateSambaAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadSambaConnectionSchema(ReadConnectionBaseSchema):
    type: SAMBA_TYPE
    data: ReadSambaConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadSambaAuthSchema | None = None


class UpdateSambaConnectionSchema(CreateSambaConnectionSchema):
    auth_data: UpdateSambaAuthSchema = Field(
        description="Credentials for authorization",
    )
