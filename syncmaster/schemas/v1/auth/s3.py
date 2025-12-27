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


class UpdateS3AuthSchema(CreateS3AuthSchema):
    secret_key: SecretStr | None = None  # type: ignore[assignment]

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("secret_key",)
