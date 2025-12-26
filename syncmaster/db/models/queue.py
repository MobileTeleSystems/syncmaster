# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from sqlalchemy import Computed, String
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from syncmaster.db.mixins import ResourceMixin, TimestampMixin
from syncmaster.db.models.base import Base
from syncmaster.db.models.group import Group


class Queue(Base, ResourceMixin, TimestampMixin):
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    slug: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)

    group: Mapped[Group] = relationship(Group)

    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            """
            -- === NAME FIELD ===
            -- Russian stemming for better morphological matching of regular words
            to_tsvector('russian', coalesce(name, ''))
            -- Simple dictionary (no stemming) for exact token match
            || to_tsvector('simple', coalesce(name, ''))
            -- Simple dictionary with translate(): split by . / - _ : \
            -- (used when 'name' contains technical fields)
            || to_tsvector(
                'simple',
                translate(coalesce(name, ''), './-_:\\', '      ')
            )
            """,
            persisted=True,
        ),
        nullable=False,
        deferred=True,
    )

    def __repr__(self):
        return f"<Queue name={self.name} slug={self.slug} description={self.description}>"
