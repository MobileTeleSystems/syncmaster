# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Annotated, Literal

from pydantic import BaseModel, Field

from syncmaster.schemas.v1.transformation_types import DATAFRAME_ROWS_FILTER


class BaseRowsFilter(BaseModel):
    field: str


class IsNullFilter(BaseRowsFilter):
    type: Literal["is_null"]


class IsNotNullFilter(BaseRowsFilter):
    type: Literal["is_not_null"]


class EqualFilter(BaseRowsFilter):
    type: Literal["equal"]
    value: str


class NotEqualFilter(BaseRowsFilter):
    type: Literal["not_equal"]
    value: str


class GreaterThanFilter(BaseRowsFilter):
    type: Literal["greater_than"]
    value: str


class GreaterOrEqualFilter(BaseRowsFilter):
    type: Literal["greater_or_equal"]
    value: str


class LessThanFilter(BaseRowsFilter):
    type: Literal["less_than"]
    value: str


class LessOrEqualFilter(BaseRowsFilter):
    type: Literal["less_or_equal"]
    value: str


class LikeFilter(BaseRowsFilter):
    type: Literal["like"]
    value: str


class ILikeFilter(BaseRowsFilter):
    type: Literal["ilike"]
    value: str


class NotLikeFilter(BaseRowsFilter):
    type: Literal["not_like"]
    value: str


class NotILikeFilter(BaseRowsFilter):
    type: Literal["not_ilike"]
    value: str


class RegexpFilter(BaseRowsFilter):
    type: Literal["regexp"]
    value: str


RowsFilter = (
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
    filters: list[Annotated[RowsFilter, Field(discriminator="type")]] = Field(default_factory=list)
