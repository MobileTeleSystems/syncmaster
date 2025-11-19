# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from syncmaster.db.models import RunType, Status
from syncmaster.schemas.v1.page import PageSchema


class CreateRunSchema(BaseModel):
    transfer_id: int = Field(description="Transfer id")


class ShortRunSchema(CreateRunSchema):
    id: int = Field(description="Run id")
    started_at: datetime | None = None
    ended_at: datetime | None = None
    status: Status
    log_url: str | None = None
    type: RunType

    model_config = ConfigDict(from_attributes=True)


class ReadRunSchema(ShortRunSchema):
    transfer_dump: dict


class RunPageSchema(PageSchema):
    items: list[ShortRunSchema]
