from pydantic import BaseModel

from app.api.v1.schemas import PageSchema


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
