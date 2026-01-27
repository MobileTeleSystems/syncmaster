# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import re
from typing import Literal

from pydantic import BaseModel, field_validator

ALLOWED_SELECT_QUERY = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


class Sql(BaseModel):
    type: Literal["sql"]
    query: str
    dialect: Literal["spark"] = "spark"

    @field_validator("query", mode="after")
    @classmethod
    def _validate_query(cls, value: str) -> str:
        if not ALLOWED_SELECT_QUERY.match(value):
            msg = f"Query must be a SELECT statement, got '{value}'"
            raise ValueError(msg)

        return value
