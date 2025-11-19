# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field, ValidationInfo, field_validator

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


class ReadS3ConnectionDataSchema(BaseModel):
    host: str
    bucket: str
    protocol: Literal["http", "https"] = "https"
    port: int | None = Field(default=None, gt=0, le=65535, validate_default=True)  # noqa: WPS432
    region: str | None = None
    bucket_style: Literal["domain", "path"] = "path"
    additional_params: dict = Field(default_factory=dict)


class CreateS3ConnectionDataSchema(ReadS3ConnectionDataSchema):
    @field_validator("port", mode="after")
    @classmethod
    def validate_port(cls, port: int | None, info: ValidationInfo) -> int:
        protocol = info.data.get("protocol")
        if port is None:
            return 443 if protocol == "https" else 80  # noqa: WPS432
        return port


class ReadS3ConnectionSchema(ReadConnectionBaseSchema):
    type: S3_TYPE = Field(description="Connection type")
    data: ReadS3ConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the S3 bucket",
    )
    auth_data: ReadS3AuthSchema | None = Field(
        default=None,
        description="Credentials for authorization",
    )


class CreateS3ConnectionSchema(CreateConnectionBaseSchema):
    type: S3_TYPE = Field(description="Connection type")
    data: CreateS3ConnectionDataSchema = Field(
        alias="connection_data",
        description="Data required to connect to the S3 bucket",
    )
    auth_data: CreateS3AuthSchema = Field(
        description="S3 bucket credentials",
    )


class UpdateS3ConnectionSchema(CreateS3ConnectionSchema):
    auth_data: UpdateS3AuthSchema = Field(
        description="S3 bucket credentials",
    )
