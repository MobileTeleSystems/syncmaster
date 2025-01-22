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


class UpdateBasicAuthSchema(BasicAuthSchema):
    user: str | None = None  # noqa: F722
    password: SecretStr | None = None
