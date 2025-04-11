# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, ConfigDict, model_validator

from syncmaster.db.models import GroupMemberRole
from syncmaster.schemas.v1.page import PageSchema
from syncmaster.schemas.v1.types import NameConstr


class UpdateGroupSchema(BaseModel):
    name: NameConstr
    description: str
    owner_id: int


class CreateGroupSchema(BaseModel):
    name: NameConstr
    description: str


class AddUserSchema(BaseModel):
    role: GroupMemberRole

    model_config = ConfigDict(from_attributes=True)

    @model_validator(mode="before")
    def validate_role(cls, values):
        if isinstance(values, dict):
            role = values.get("role")
        else:
            # access 'role' directly if 'values' is an object
            role = getattr(values, "role", None)

        if role and not GroupMemberRole.is_public_role(role):
            raise ValueError(
                f"Input should be one of: {GroupMemberRole.public_roles_str()}",
            )
        return values


class ReadGroupSchema(BaseModel):
    id: int
    name: str
    description: str
    owner_id: int

    model_config = ConfigDict(from_attributes=True)


class GroupWithUserRoleSchema(BaseModel):
    data: ReadGroupSchema
    role: GroupMemberRole

    model_config = ConfigDict(from_attributes=True)


class GroupPageSchema(PageSchema):
    items: list[GroupWithUserRoleSchema]
