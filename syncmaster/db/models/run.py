# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import JSON, BigInteger, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import ChoiceType

from syncmaster.db.mixins import TimestampMixin
from syncmaster.db.models.base import Base
from syncmaster.db.models.transfer import Transfer


class Status(enum.StrEnum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    FAILED = "FAILED"
    SEND_STOP_SIGNAL = "SEND_STOP_SIGNAL"
    STOPPED = "STOPPED"
    FINISHED = "FINISHED"


class RunType(enum.StrEnum):
    MANUAL = "MANUAL"
    SCHEDULED = "SCHEDULED"


class Run(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )
    transfer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("transfer.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )
    status: Mapped[Status] = mapped_column(
        ChoiceType(Status),
        nullable=False,
        default=Status.CREATED,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=RunType.MANUAL,
        index=True,
    )
    log_url: Mapped[str] = mapped_column(String(512), nullable=True)
    transfer_dump: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})

    transfer: Mapped[Transfer] = relationship(Transfer)

    def __repr__(self):
        return (
            f"<Run "
            f"id={self.id} "
            f"transfer_id={self.transfer_id} "
            f"type={self.type} "
            f"created_at={self.created_at:%Y-%m-%d %H:%M:%S}>"
        )
