# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.transformation_types import DATAFRAME_ROWS_FILTER


class BaseRowFilter(BaseModel):
    field: str


class IsNullFilter(BaseRowFilter):
    type: Literal["is_null"]


class IsNotNullFilter(BaseRowFilter):
    type: Literal["is_not_null"]


class EqualFilter(BaseRowFilter):
    type: Literal["equal"]
    value: str


class NotEqualFilter(BaseRowFilter):
    type: Literal["not_equal"]
    value: str


class GreaterThanFilter(BaseRowFilter):
    type: Literal["greater_than"]
    value: str


class GreaterOrEqualFilter(BaseRowFilter):
    type: Literal["greater_or_equal"]
    value: str


class LessThanFilter(BaseRowFilter):
    type: Literal["less_than"]
    value: str


class LessOrEqualFilter(BaseRowFilter):
    type: Literal["less_or_equal"]
    value: str


class LikeFilter(BaseRowFilter):
    type: Literal["like"]
    value: str


class ILikeFilter(BaseRowFilter):
    type: Literal["ilike"]
    value: str


class NotLikeFilter(BaseRowFilter):
    type: Literal["not_like"]
    value: str


class NotILikeFilter(BaseRowFilter):
    type: Literal["not_ilike"]
    value: str


class RegexpFilter(BaseRowFilter):
    type: Literal["regexp"]
    value: str


RowFilter = (
    IsNullFilter
    | IsNotNullFilter
    | EqualFilter
    | NotEqualFilter
    | GreaterThanFilter
    | GreaterOrEqualFilter
    | LessThanFilter
    | LessOrEqualFilter
    | LikeFilter
    | ILikeFilter
    | NotLikeFilter
    | NotILikeFilter
    | RegexpFilter
)


class DataframeRowsFilter(BaseModel):
    type: DATAFRAME_ROWS_FILTER
    filters: list[Annotated[RowFilter, Field(..., discriminator="type")]] = Field(default_factory=list)
