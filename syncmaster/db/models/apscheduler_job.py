# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from sqlalchemy import Float, Index, LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from syncmaster.db.models.base import Base


class APSchedulerJob(Base):
    __tablename__ = "apscheduler_jobs"

    id: Mapped[str] = mapped_column(String(191), primary_key=True, nullable=False)
    next_run_time: Mapped[float | None] = mapped_column(Float(25), nullable=True)
    job_state: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    __table_args__ = (Index("ix_apscheduler_jobs_next_run_time", "next_run_time"),)
