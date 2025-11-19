# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class ReadS3AuthSchema(BaseModel):
    type: Literal["s3"] = Field(description="Auth type")
    access_key: str


class CreateS3AuthSchema(ReadS3AuthSchema):
    secret_key: SecretStr


class UpdateS3AuthSchema(ReadS3AuthSchema):
    secret_key: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("secret_key",)
