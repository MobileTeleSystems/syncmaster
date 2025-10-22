# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, SecretStr


class S3AuthSchema(BaseModel):
    type: Literal["s3"]


class CreateS3AuthSchema(S3AuthSchema):
    access_key: str
    secret_key: SecretStr


class ReadS3AuthSchema(S3AuthSchema):
    access_key: str


class UpdateS3AuthSchema(CreateS3AuthSchema):
    secret_key: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("secret_key",)
