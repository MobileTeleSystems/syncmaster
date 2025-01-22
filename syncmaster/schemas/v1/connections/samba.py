# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateSambaAuthSchema,
    ReadSambaAuthSchema,
    UpdateSambaAuthSchema,
)
from syncmaster.schemas.v1.connection_types import SAMBA_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
    UpdateConnectionBaseSchema,
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


class UpdateSambaConnectionDataSchema(BaseModel):
    host: str | None = None
    share: str | None = None
    port: int | None = None
    protocol: Literal["SMB", "NetBIOS"] | None = None
    domain: str | None = None


class CreateSambaConnectionSchema(CreateConnectionBaseSchema):
    type: SAMBA_TYPE = Field(..., description="Connection type")
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


class UpdateSambaConnectionSchema(UpdateConnectionBaseSchema):
    type: SAMBA_TYPE
    data: UpdateSambaConnectionDataSchema | None = Field(alias="connection_data", default=None)
    auth_data: UpdateSambaAuthSchema | None = None
