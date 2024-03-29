# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field, constr

from syncmaster.schemas.v1.page import PageSchema


class CreateQueueSchema(BaseModel):
    name: constr(max_length=128, pattern=r"^[-_a-zA-Z0-9]+$") = Field(  # noqa: F722
        ...,
        description="Queue name",
    )
    group_id: int = Field(..., description="Queue owner group id")
    description: str = Field(default="", description="Additional description")


class ReadQueueSchema(BaseModel):
    name: str
    description: str | None = None
    group_id: int
    id: int

    class Config:
        from_attributes = True


class QueuePageSchema(PageSchema):
    items: list[ReadQueueSchema]


class UpdateQueueSchema(BaseModel):
    description: str | None = None
