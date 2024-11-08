# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field, computed_field, constr

from syncmaster.schemas.v1.page import PageSchema


class CreateQueueSchema(BaseModel):
    name: constr(max_length=128, pattern=r"^[-_a-zA-Z0-9]+$") = Field(  # noqa: F722
        ...,
        description="Queue name that allows letters, numbers, dashes, and underscores",
    )
    group_id: int = Field(..., description="Queue owner group id")
    description: str = Field(default="", description="Additional description")

    @computed_field
    @property
    def slug(self) -> str:
        return f"{self.group_id}-{self.name}"


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
