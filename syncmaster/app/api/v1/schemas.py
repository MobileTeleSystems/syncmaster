import abc
from typing import Any, Literal

from pydantic import BaseModel

from app.db.models import ObjectType, Rule
from app.db.utils import Pagination

# transfer types
FULL_TYPE = Literal["full"]
INCREMENTAL_TYPE = Literal["incremental"]


# connection types
POSTGRES_TYPE = Literal["postgres"]
ORACLE_TYPE = Literal["oracle"]


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


class SetRuleSchema(BaseModel):
    user_id: int
    rule: Rule


class ReadAclSchema(BaseModel):
    object_id: int
    object_type: ObjectType
    user_id: int
    rule: Rule

    class Config:
        orm_mode = True


class AclPageSchema(PageSchema):
    items: list[ReadAclSchema]
