from pydantic import BaseModel, constr

from app.api.v1.schemas import PageSchema


class CreateQueueSchema(BaseModel):
    name: constr(max_length=128, regex=r"^[-_a-zA-Z0-9]+$")  # type: ignore # noqa: F722
    group_id: int
    description: str = ""


class ReadQueueSchema(BaseModel):
    name: str
    description: str | None
    group_id: int
    id: int

    class Config:
        orm_mode = True


class QueuePageSchema(PageSchema):
    items: list[ReadQueueSchema]


class UpdateQueueSchema(BaseModel):
    description: str | None = None
