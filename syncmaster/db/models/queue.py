# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Computed, String
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from syncmaster.db.mixins import ResourceMixin, TimestampMixin
from syncmaster.db.models.base import Base

if TYPE_CHECKING:
    from syncmaster.db.models.group import Group
    from syncmaster.db.models.transfer import Transfer


class Queue(Base, ResourceMixin, TimestampMixin):
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)

    transfers: Mapped[list[Transfer]] = relationship(back_populates="queue")
    group: Mapped[Group] = relationship(back_populates="queue")

    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english'::regconfig, name)", persisted=True),
        nullable=False,
        deferred=True,
        doc="Full-text search vector",
    )

    def __repr__(self):
        return f"<Queue name={self.name} slug={self.slug} description={self.description}>"
