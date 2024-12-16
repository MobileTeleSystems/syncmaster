# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import Any

from sqlalchemy import JSON, Computed, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from syncmaster.db.mixins import ResourceMixin, TimestampMixin
from syncmaster.db.models.base import Base
from syncmaster.db.models.group import Group


class Connection(Base, ResourceMixin, TimestampMixin):
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})

    group: Mapped[Group] = relationship("Group")

    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            """
            to_tsvector(
                'english'::regconfig,
                name || ' ' ||
                COALESCE(json_extract_path_text(data, 'host'), '') || ' ' ||
                COALESCE(translate(json_extract_path_text(data, 'host'), '.', ' '), '')
            )
            """,
            persisted=True,
        ),
        nullable=False,
        deferred=True,
    )

    def __repr__(self):
        return f"<Connection " f"name={self.name} " f"description={self.description} " f"group_id={self.group_id}>"

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            UniqueConstraint("name", "group_id"),
            Index("idx_connection_search_vector", "search_vector", postgresql_using="gin"),
        )
