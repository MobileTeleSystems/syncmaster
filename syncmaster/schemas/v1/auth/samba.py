# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class ReadSambaAuthSchema(BaseModel):
    type: Literal["samba"] = Field(description="Auth type")
    user: str
    auth_type: Literal["NTLMv1", "NTLMv2"] = "NTLMv2"


class CreateSambaAuthSchema(ReadSambaAuthSchema):
    password: SecretStr


class UpdateSambaAuthSchema(ReadSambaAuthSchema):
    password: SecretStr | None = None

    def get_secret_fields(self) -> tuple[str, ...]:
        return ("password",)
