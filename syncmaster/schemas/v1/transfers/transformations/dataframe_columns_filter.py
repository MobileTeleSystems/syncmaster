# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.transformation_types import DATAFRAME_COLUMNS_FILTER


class BaseColumnsFilter(BaseModel):
    field: str


class IncludeFilter(BaseColumnsFilter):
    type: Literal["include"]


class RenameFilter(BaseColumnsFilter):
    type: Literal["rename"]
    to: str


class CastFilter(BaseColumnsFilter):
    type: Literal["cast"]
    as_type: str


ColumnsFilter = IncludeFilter | RenameFilter | CastFilter


class DataframeColumnsFilter(BaseModel):
    type: DATAFRAME_COLUMNS_FILTER
    filters: list[Annotated[ColumnsFilter, Field(discriminator="type")]] = Field(default_factory=list)
