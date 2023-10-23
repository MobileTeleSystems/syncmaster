from pydantic import BaseModel

from app.api.v1.schemas import PageSchema


class CreateQueueSchema(BaseModel):
    name: str
    description: str | None
    is_active: bool = True


class ReadQueueSchema(BaseModel):
    name: str
    description: str | None
    is_active: bool
    id: int

    class Config:
        orm_mode = True


class QueuePageSchema(PageSchema):
    items: list[ReadQueueSchema]


class UpdateQueueSchema(BaseModel):
    name: str | None = None
    description: str | None = None
    is_active: bool | None = None
