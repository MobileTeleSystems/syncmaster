# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, SecretStr, field_serializer


class SecretDumpMixin(BaseModel):

    @field_serializer("*", when_used="json")
    def dump_secrets(self, value):
        if isinstance(value, SecretStr):
            return value.get_secret_value()
        return value
