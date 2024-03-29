# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel

from syncmaster.db.models import GroupMemberRole
from syncmaster.schemas.v1.page import PageSchema
from syncmaster.schemas.v1.types import NameConstr


class UpdateGroupSchema(BaseModel):
    name: NameConstr  # noqa: F722
    description: str
    owner_id: int


class CreateGroupSchema(BaseModel):
    name: NameConstr  # noqa: F722
    description: str


class AddUserSchema(BaseModel):
    role: GroupMemberRole

    class Config:
        from_attributes = True


class ReadGroupSchema(BaseModel):
    id: int
    name: NameConstr  # noqa: F722
    description: str
    owner_id: int

    class Config:
        from_attributes = True


class GroupPageSchema(PageSchema):
    items: list[ReadGroupSchema]
