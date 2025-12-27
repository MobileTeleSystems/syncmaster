# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import Field, SecretStr

from syncmaster.schemas.v1.auth.mixins import SecretDumpMixin


class ReadBasicAuthSchema(SecretDumpMixin):
    type: Literal["basic"] = Field(description="Auth type")
    user: str


class CreateBasicAuthSchema(ReadBasicAuthSchema):
    password: SecretStr


class UpdateBasicAuthSchema(CreateBasicAuthSchema):
    password: SecretStr | None = None  # type: ignore[assignment]

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("password",)
