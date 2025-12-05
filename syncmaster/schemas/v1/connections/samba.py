# SPDX-FileCopyrightText: 2023-present MTS PJSC
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


class SambaConnectionDataSchema(BaseModel):
    host: str
    share: str
    port: int | None = Field(default=None, gt=0, le=65535)  # noqa: WPS432
    protocol: Literal["SMB", "NetBIOS"] = "SMB"
    domain: str = ""


class CreateSambaConnectionSchema(CreateConnectionBaseSchema):
    type: SAMBA_TYPE = Field(description="Connection type")
    data: SambaConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the remote server",
    )
    auth_data: CreateSambaAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadSambaConnectionSchema(ReadConnectionBaseSchema):
    type: SAMBA_TYPE = Field(description="Connection type")
    data: SambaConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadSambaAuthSchema | None = None


class UpdateSambaConnectionSchema(CreateSambaConnectionSchema):
    auth_data: UpdateSambaAuthSchema = Field(
        description="Credentials for authorization",
    )
