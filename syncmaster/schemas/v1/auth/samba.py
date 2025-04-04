# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Literal

from pydantic import BaseModel, SecretStr


class SambaAuthSchema(BaseModel):
    type: Literal["samba"]


class CreateSambaAuthSchema(SambaAuthSchema):
    user: str
    password: SecretStr
    auth_type: Literal["NTLMv1", "NTLMv2"] = "NTLMv2"


class ReadSambaAuthSchema(SambaAuthSchema):
    user: str
    auth_type: Literal["NTLMv1", "NTLMv2"]


class UpdateSambaAuthSchema(CreateSambaAuthSchema):
    password: SecretStr | None = None

    @property
    def secret_field(self) -> str:
        return "password"
