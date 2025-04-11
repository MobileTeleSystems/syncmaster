# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field, model_validator

from syncmaster.schemas.v1.auth import (
    CreateS3AuthSchema,
    ReadS3AuthSchema,
)
from syncmaster.schemas.v1.auth.s3 import UpdateS3AuthSchema
from syncmaster.schemas.v1.connection_types import S3_TYPE
from syncmaster.schemas.v1.connections.connection_base import (
    CreateConnectionBaseSchema,
    ReadConnectionBaseSchema,
)


class CreateS3ConnectionDataSchema(BaseModel):
    host: str
    bucket: str
    port: int | None = None
    region: str | None = None
    protocol: Literal["http", "https"] = "https"
    bucket_style: Literal["domain", "path"] = "domain"

    @model_validator(mode="before")
    def validate_port(cls, values: dict) -> dict:
        port = values.get("port")
        protocol = values.get("protocol")

        if port is None:
            port = 443 if protocol == "https" else 80  # noqa: WPS432
            values["port"] = port

        return values


class ReadS3ConnectionDataSchema(BaseModel):
    host: str
    bucket: str
    port: int | None = None
    region: str | None = None
    protocol: Literal["http", "https"] = "https"
    bucket_style: Literal["domain", "path"] = "domain"


class CreateS3ConnectionSchema(CreateConnectionBaseSchema):
    type: S3_TYPE = Field(description="Connection type")
    data: CreateS3ConnectionDataSchema = Field(
        ...,
        alias="connection_data",
        description=(
            "Data required to connect to the S3 bucket. These are the parameters that are specified in the URL request."
        ),
    )
    auth_data: CreateS3AuthSchema = Field(
        ...,
        discriminator="type",
        description="Credentials for authorization",
    )


class ReadS3ConnectionSchema(ReadConnectionBaseSchema):
    type: S3_TYPE
    data: ReadS3ConnectionDataSchema = Field(alias="connection_data")
    auth_data: ReadS3AuthSchema | None = Field(discriminator="type", default=None)


class UpdateS3ConnectionSchema(CreateS3ConnectionSchema):
    auth_data: UpdateS3AuthSchema = Field(
        description="Credentials for authorization",
    )
