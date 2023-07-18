import abc
from typing import Any

from pydantic import BaseModel

from app.db.utils import Pagination


class StatusResponseSchema(BaseModel):
    ok: bool
    status_code: int
    message: str


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
