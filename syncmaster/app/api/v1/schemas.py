import abc
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel

from app.db.models import Acl, ObjectType
from app.db.utils import Pagination

# transfer types
FULL_TYPE = Literal["full"]
INCREMENTAL_TYPE = Literal["incremental"]


# connection types
HIVE_TYPE = Literal["hive"]
ORACLE_TYPE = Literal["oracle"]
POSTGRES_TYPE = Literal["postgres"]


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


class UserRule(str, Enum):
    READ = "READ"
    WRITE = "WRITE"
    DELETE = "DELETE"

    @classmethod
    def from_int(cls, item: Any):
        rule = item.rule

        if rule == 0:
            item.rule = UserRule.READ
        if rule == 1:
            item.rule = UserRule.WRITE
        if rule == 2:
            item.rule = UserRule.DELETE

        return item


class SetRuleSchema(BaseModel):
    user_id: int
    rule: UserRule


class ReadRuleSchema(BaseModel):
    object_id: int
    object_type: ObjectType
    user_id: int
    rule: UserRule

    class Config:
        orm_mode = True

    @classmethod
    def from_acl(cls, acl: Acl):
        """Convert rule from int to str"""
        acl = UserRule.from_int(acl)

        return ReadRuleSchema.from_orm(acl)


class AclPageSchema(PageSchema):
    items: list[ReadRuleSchema]

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
            items=[UserRule.from_int(item) for item in pagination.items],
        )
