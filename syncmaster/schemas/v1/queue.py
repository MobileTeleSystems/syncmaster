# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field, constr, model_validator
from pydantic.json_schema import SkipJsonSchema

from syncmaster.schemas.v1.page import PageSchema


class CreateQueueSchema(BaseModel):
    name: constr(max_length=128, pattern=r"^[-_a-zA-Z0-9]+$") = Field(  # noqa: F722
        ...,
        description="Queue name that allows letters, numbers, dashes, and underscores",
    )
    group_id: int = Field(..., description="Queue owner group id")
    description: str = Field(default="", description="Additional description")
    slug: SkipJsonSchema[str] = Field(description="Generated slug for unique queue identification")

    @model_validator(mode="before")
    def generate_slug(cls, values):
        if "group_id" not in values or "name" not in values:
            raise ValueError("Fields name and group_id are required")
        values["slug"] = f"{values["group_id"]}-{values["name"]}"
        return values


class ReadQueueSchema(BaseModel):
    name: str
    slug: str
    description: str | None = None
    group_id: int
    id: int

    class Config:
        from_attributes = True


class QueuePageSchema(PageSchema):
    items: list[ReadQueueSchema]


class UpdateQueueSchema(BaseModel):
    description: str | None = None
