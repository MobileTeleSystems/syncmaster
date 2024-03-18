# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel

from syncmaster.db import GroupMemberRole
from syncmaster.schemas.v1.schemas import NameConstr, PageSchema


class UpdateGroupSchema(BaseModel):
    name: NameConstr  # type: ignore # noqa: F722
    description: str
    owner_id: int


class CreateGroupSchema(BaseModel):
    name: NameConstr  # type: ignore # noqa: F722
    description: str


class AddUserSchema(BaseModel):
    role: GroupMemberRole

    class Config:
        orm_mode = True


class ReadGroupSchema(BaseModel):
    id: int
    name: NameConstr  # type: ignore # noqa: F722
    description: str
    owner_id: int

    class Config:
        orm_mode = True


class GroupPageSchema(PageSchema):
    items: list[ReadGroupSchema]
