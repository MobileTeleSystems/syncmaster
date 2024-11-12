# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from sqlalchemy import BigInteger, Boolean, String
from sqlalchemy.orm import Mapped, mapped_column

from syncmaster.db.mixins import DeletableMixin, TimestampMixin
from syncmaster.db.models.base import Base


class User(Base, TimestampMixin, DeletableMixin):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    email: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    first_name: Mapped[str] = mapped_column(String(256))
    last_name: Mapped[str] = mapped_column(String(256))
    middle_name: Mapped[str] = mapped_column(String(256))
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"User(username={self.username}, is_superuser={self.is_superuser}, is_active={self.is_active})"
