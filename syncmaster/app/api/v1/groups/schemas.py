# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel

from app.api.v1.schemas import NameConstr, PageSchema
from app.db.models import GroupMemberRole


class UpdateGroupSchema(BaseModel):
    name: NameConstr  # type: ignore # noqa: F722
    description: str
    owner_id: int


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
