# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ConfigDict

from syncmaster.db.models import GroupMemberRole
from syncmaster.db.utils import Pagination
from syncmaster.schemas.v1.page import MetaPageSchema, PageSchema


class ReadGroupMember(BaseModel):
    id: int
    username: str
    role: GroupMemberRole

    model_config = ConfigDict(from_attributes=True)


class ReadUserSchema(BaseModel):
    id: int
    username: str
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)


class FullUserSchema(ReadGroupMember):
    is_active: bool


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
