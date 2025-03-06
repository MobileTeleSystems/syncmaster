# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
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
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

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
    queue: Mapped[Queue] = relationship(back_populates="transfers")

    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed(
            """
            to_tsvector(
                'english'::regconfig,
                name || ' ' ||
                COALESCE(json_extract_path_text(source_params, 'table_name'), '') || ' ' ||
                COALESCE(json_extract_path_text(target_params, 'table_name'), '') || ' ' ||
                COALESCE(json_extract_path_text(source_params, 'directory_path'), '') || ' ' ||
                COALESCE(json_extract_path_text(target_params, 'directory_path'), '') || ' ' ||
                translate(name, './', '  ') || ' ' ||
                COALESCE(translate(json_extract_path_text(source_params, 'table_name'), './', '  '), '') || ' ' ||
                COALESCE(translate(json_extract_path_text(target_params, 'table_name'), './', '  '), '') || ' ' ||
                COALESCE(translate(json_extract_path_text(source_params, 'directory_path'), './', '  '), '') || ' ' ||
                COALESCE(translate(json_extract_path_text(target_params, 'directory_path'), './', '  '), '')
            )
            """,
            persisted=True,
        ),
        nullable=False,
        deferred=True,
    )

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (
            UniqueConstraint("name", "group_id"),
            Index("idx_transfer_search_vector", "search_vector", postgresql_using="gin"),
        )
