# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, SecretStr, model_validator

from syncmaster.schemas.v1.connection_types import S3_TYPE


class S3BaseSchema(BaseModel):
    type: S3_TYPE

    class Config:
        from_attributes = True


class S3ReadConnectionSchema(S3BaseSchema):
    host: str
    bucket: str
    port: int | None = None
    region: str | None = None
    protocol: Literal["http", "https"] = "https"
    bucket_style: Literal["domain", "path"] = "domain"


class S3CreateConnectionSchema(S3BaseSchema):
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
            port = 443 if protocol == "https" else 80
            values["port"] = port

        return values


class S3UpdateConnectionSchema(S3BaseSchema):
    host: str | None = None
    bucket: str | None = None
    port: int | None = None
    region: str | None = None
    protocol: Literal["http", "https"] | None = None
    bucket_style: Literal["domain", "path"] | None = None


class S3CreateAuthSchema(S3BaseSchema):
    access_key: str
    secret_key: SecretStr


class S3ReadAuthSchema(S3BaseSchema):
    access_key: str


class S3UpdateAuthSchema(S3BaseSchema):
    access_key: str | None = None
    secret_key: SecretStr | None = None
