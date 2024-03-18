# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import abc
from typing import Any, Literal

from pydantic import BaseModel, constr

from syncmaster.db import Pagination

# transfer types
FULL_TYPE = Literal["full"]
INCREMENTAL_TYPE = Literal["incremental"]


# connection types
HIVE_TYPE = Literal["hive"]
ORACLE_TYPE = Literal["oracle"]
POSTGRES_TYPE = Literal["postgres"]
S3_TYPE = Literal["s3"]
HDFS_TYPE = Literal["hdfs"]

# file formats
CSV_FORMAT = Literal["csv"]
JSONLINE_FORMAT = Literal["jsonline"]
JSON_FORMAT = Literal["json"]


NameConstr = constr(min_length=1)


class StatusResponseSchema(BaseModel):
    ok: bool
    status_code: int
    message: str


class StatusCopyTransferResponseSchema(StatusResponseSchema):
    source_connection_id: int
    target_connection_id: int
    copied_transfer_id: int


class MetaPageSchema(BaseModel):
    page: int
    pages: int
    total: int
    page_size: int
    has_next: bool
    has_previous: bool
    next_page: int | None
    previous_page: int | None


class PageSchema(BaseModel, abc.ABC):
    meta: MetaPageSchema
    items: list[Any]

    @classmethod
    def from_pagination(cls, pagination: Pagination):
        return cls(
            meta=MetaPageSchema(
                page=pagination.page,
                pages=pagination.pages,
                page_size=pagination.page_size,
                total=pagination.total,
                has_next=pagination.has_next,
                has_previous=pagination.has_previous,
                next_page=pagination.next_page,
                previous_page=pagination.previous_page,
            ),
            items=pagination.items,
        )
