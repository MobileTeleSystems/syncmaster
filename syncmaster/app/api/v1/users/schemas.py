from string import ascii_lowercase, digits

from pydantic import BaseModel, validator

from app.api.v1.schemas import MetaPageSchema, PageSchema
from app.db.models import GroupMemberRole
from app.db.utils import Pagination


class UpdateUserSchema(BaseModel):
    username: str

    @validator("username")
    def username_validator(cls, value):
        alph = ascii_lowercase + digits + "_"
        if any(filter(lambda x: x not in alph, value)):
            raise ValueError("Invalid username")
        return value


class ReadGroupMember(BaseModel):
    id: int
    username: str
    role: GroupMemberRole

    class Config:
        orm_mode = True


class ReadUserSchema(BaseModel):
    id: int
    username: str
    is_superuser: bool

    class Config:
        orm_mode = True


class FullUserSchema(ReadGroupMember):
    is_active: bool

    class Config:
        orm_mode = True


class UserPageSchemaAsGroupMember(PageSchema):
    items: list[ReadGroupMember]

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
            items=[
                ReadGroupMember(
                    id=user.id,
                    username=user.username,
                    role=role,
                )
                for user, role in pagination.items
            ],
        )


class UserPageSchema(PageSchema):
    items: list[ReadUserSchema]

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
