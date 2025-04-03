# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from syncmaster.db.models import RunType, Status
from syncmaster.schemas.v1.page import PageSchema


class ShortRunSchema(BaseModel):
    id: int
    transfer_id: int
    started_at: datetime | None = None
    ended_at: datetime | None = None
    status: Status
    log_url: str | None = None
    type: RunType


class RunPageSchema(PageSchema):
    items: list[ShortRunSchema]


class ReadRunSchema(ShortRunSchema):
    transfer_dump: dict


class CreateRunSchema(BaseModel):
    transfer_id: int
