# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import re
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, computed_field

from syncmaster.schemas.v1.page import PageSchema

ALLOWED_PATTERN = re.compile(r"^[ -~]+$")
RESTRICTED_PATTERN = re.compile(r"[^a-zA-Z0-9]+")

QueueName = Annotated[
    str,
    StringConstraints(min_length=3, max_length=128, pattern=ALLOWED_PATTERN),  # noqa: WPS432
]


class CreateQueueSchema(BaseModel):
    name: QueueName = Field(
        description="Queue name that allows letters, numbers, dashes, and underscores",
    )
    group_id: int = Field(description="Queue owner group id")
    description: str = Field(default="", description="Additional description")

    @computed_field
    @property
    def slug(self) -> str:
        short_name = RESTRICTED_PATTERN.sub("_", self.name.lower()).strip("_")
        return f"{self.group_id}-{short_name}"


class ReadQueueSchema(BaseModel):
    name: str
    slug: str
    description: str | None = None
    group_id: int
    id: int

    model_config = ConfigDict(from_attributes=True)


class QueuePageSchema(PageSchema):
    items: list[ReadQueueSchema]


class UpdateQueueSchema(BaseModel):
    name: QueueName
    description: str = ""
