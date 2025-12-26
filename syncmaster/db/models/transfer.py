# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Computed,
    ForeignKey,
    Index,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship

from syncmaster.db.mixins import ResourceMixin, TimestampMixin
from syncmaster.db.models.base import Base
from syncmaster.db.models.group import Group

if TYPE_CHECKING:
    from syncmaster.db.models.connection import Connection
    from syncmaster.db.models.queue import Queue


class Transfer(
    Base,
    ResourceMixin,
    TimestampMixin,
):
    __table_args__ = (
        UniqueConstraint("name", "group_id"),
        Index("idx_transfer_search_vector", "search_vector", postgresql_using="gin"),
    )

    source_connection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("connection.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    target_connection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("connection.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strategy_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    source_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    target_params: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    transformations: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False, default=list)
    resources: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    is_scheduled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    schedule: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    queue_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("queue.id", ondelete="CASCADE"),
        nullable=False,
    )

    group: Mapped[Group] = relationship(Group)
    source_connection: Mapped[Connection] = relationship(foreign_keys=source_connection_id)
    target_connection: Mapped[Connection] = relationship(foreign_keys=target_connection_id)
    queue: Mapped[Queue] = relationship(Queue)

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

            -- === TABLE NAME FIELDS ===
            -- Simple dictionary (no stemming) for exact match
            || to_tsvector('simple', coalesce(source_params->>'table_name', ''))
            || to_tsvector('simple', coalesce(target_params->>'table_name', ''))
            -- Simple dictionary with translate(): split by . / - _ : \\ for partial token matching
            || to_tsvector(
                'simple',
                translate(coalesce(source_params->>'table_name', ''), './-_:\\', '      ')
            )
            || to_tsvector(
                'simple',
                translate(coalesce(target_params->>'table_name', ''), './-_:\\', '      ')
            )

            -- === DIRECTORY PATH FIELDS ===
            -- Simple dictionary (no stemming) for exact match
            || to_tsvector('simple', coalesce(source_params->>'directory_path', ''))
            || to_tsvector('simple', coalesce(target_params->>'directory_path', ''))
            -- Simple dictionary with translate(): split by . / - _ : \\ for partial token matching
            || to_tsvector(
                'simple',
                translate(coalesce(source_params->>'directory_path', ''), './-_:\\', '      ')
            )
            || to_tsvector(
                'simple',
                translate(coalesce(target_params->>'directory_path', ''), './-_:\\', '      ')
            )
            """,
            persisted=True,
        ),
        nullable=False,
        deferred=True,
    )
