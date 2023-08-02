from pydantic import BaseModel

from app.api.v1.schemas import PageSchema
from app.db.models import ObjectType, Rule


class UpdateGroupSchema(BaseModel):
    name: str
    description: str
    admin_id: int


class ReadGroupSchema(BaseModel):
    id: int
    name: str
    description: str
    admin_id: int

    class Config:
        orm_mode = True


class GroupPageSchema(PageSchema):
    items: list[ReadGroupSchema]


class ReadAclSchema(BaseModel):
    object_id: int
    object_type: ObjectType
    user_id: int
    rule: Rule

    class Config:
        orm_mode = True


class AclPageSchema(PageSchema):
    items: list[ReadAclSchema]
