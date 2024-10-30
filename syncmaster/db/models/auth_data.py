# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from sqlalchemy import BigInteger, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from syncmaster.db.mixins import TimestampMixin
from syncmaster.db.models.base import Base


class AuthData(Base, TimestampMixin):
    connection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("connection.id", ondelete="CASCADE"),
        primary_key=True,
    )
    value: Mapped[str] = mapped_column(nullable=False)
