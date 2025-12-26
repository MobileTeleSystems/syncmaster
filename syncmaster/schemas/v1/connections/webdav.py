# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from typing import Literal

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.auth import (
    CreateBasicAuthSchema,
    ReadBasicAuthSchema,
    UpdateBasicAuthSchema,
)
from syncmaster.schemas.v1.connection_types import WEBDAV_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class WebDAVConnectionDataSchema(BaseModel):
    host: str
    port: int | None = Field(default=None, gt=0, le=65535)
    protocol: Literal["http", "https"] = "https"


class CreateWebDAVConnectionSchema(CreateConnectionBaseSchema):
    type: WEBDAV_TYPE = Field(description="Connection type")
    data: WebDAVConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the remote server",
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadWebDAVConnectionSchema(ReadConnectionBaseSchema):
    type: WEBDAV_TYPE = Field(description="Connection type")
    data: WebDAVConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the remote server",
    )
    auth_data: ReadBasicAuthSchema | None = Field(
        default=None,
        description="Credentials for authorization",
    )


class UpdateWebDAVConnectionSchema(CreateWebDAVConnectionSchema):
    auth_data: UpdateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )
