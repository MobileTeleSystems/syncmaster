# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import Field, SecretStr

from syncmaster.schemas.v1.auth.mixins import SecretDumpMixin


class ReadS3AuthSchema(SecretDumpMixin):
    type: Literal["s3"] = Field(description="Auth type")
    access_key: str


class CreateS3AuthSchema(ReadS3AuthSchema):
    secret_key: SecretStr


class UpdateS3AuthSchema(ReadS3AuthSchema):
    secret_key: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("secret_key",)
