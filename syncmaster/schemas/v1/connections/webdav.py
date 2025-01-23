# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
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
    UpdateConnectionBaseSchema,
)


class CreateWebDAVConnectionDataSchema(BaseModel):
    host: str
    port: int | None = None
    protocol: Literal["http", "https"] = "https"


class ReadWebDAVConnectionDataSchema(BaseModel):
    host: str
    port: int | None
    protocol: Literal["http", "https"]


class UpdateWebDAVConnectionDataSchema(BaseModel):
    host: str | None = None
    port: int | None = None
    protocol: Literal["http", "https"] | None = None


class CreateWebDAVConnectionSchema(CreateConnectionBaseSchema):
    type: WEBDAV_TYPE = Field(..., description="Connection type")
    data: CreateWebDAVConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the remote server. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateBasicAuthSchema = Field(
        description="Credentials for authorization",
    )


class ReadWebDAVConnectionSchema(ReadConnectionBaseSchema):
    type: WEBDAV_TYPE
    data: ReadWebDAVConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadBasicAuthSchema | None = None


class UpdateWebDAVConnectionSchema(UpdateConnectionBaseSchema):
    type: WEBDAV_TYPE
    data: UpdateWebDAVConnectionDataSchema | None = Field(alias="connection_data", default=None)
    auth_data: UpdateBasicAuthSchema | None = None
