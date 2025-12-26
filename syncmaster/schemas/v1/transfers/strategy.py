# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated, Literal

from pydantic import BaseModel, Field


class FullStrategy(BaseModel):
    type: Literal["full"] = "full"


class IncrementalStrategy(BaseModel):
    type: Literal["incremental"] = "incremental"
    increment_by: str


Strategy = Annotated[FullStrategy | IncrementalStrategy, Field(discriminator="type")]

__all__ = [
    "FullStrategy",
    "IncrementalStrategy",
    "Strategy",
]
