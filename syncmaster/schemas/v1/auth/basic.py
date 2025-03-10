# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, SecretStr


class BasicAuthSchema(BaseModel):
    type: Literal["basic"]


class CreateBasicAuthSchema(BasicAuthSchema):
    user: str
    password: SecretStr


class ReadBasicAuthSchema(BasicAuthSchema):
    user: str


class UpdateBasicAuthSchema(CreateBasicAuthSchema):
    password: SecretStr | None = None

    @property
    def secret_field(self) -> str:
        return "password"
