# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, SecretStr


class TokenPayloadSchema(BaseModel):
    user_id: int


class AuthTokenSchema(BaseModel):
    access_token: str
    token_type: str
    expires_at: float


class BasicAuthSchema(BaseModel):
    type: Literal["basic"]


class CreateBasicAuthSchema(BasicAuthSchema):
    user: str
    password: SecretStr


class ReadBasicAuthSchema(BasicAuthSchema):
    user: str


class UpdateBasicAuthSchema(BasicAuthSchema):
    user: str | None = None  # noqa: F722
    password: SecretStr | None = None


class S3AuthSchema(BaseModel):
    type: Literal["s3"]


class CreateS3AuthSchema(S3AuthSchema):
    access_key: str
    secret_key: SecretStr


class ReadS3AuthSchema(S3AuthSchema):
    access_key: str


class UpdateS3AuthSchema(S3AuthSchema):
    access_key: str | None = None
    secret_key: SecretStr | None = None
