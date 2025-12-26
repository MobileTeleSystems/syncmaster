# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Computed, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import ChoiceType

from syncmaster.db.mixins import ResourceMixin, TimestampMixin
from syncmaster.db.models.base import Base
from syncmaster.db.models.group import Group


class ConnectionType(StrEnum):
    POSTGRES = "postgres"
    HIVE = "hive"
    ICEBERG = "iceberg"
    ORACLE = "oracle"
    CLICKHOUSE = "clickhouse"
    MSSQL = "mssql"
    MYSQL = "mysql"
    S3 = "s3"
    HDFS = "hdfs"
    SFTP = "sftp"
    FTP = "ftp"
    FTPS = "ftps"
    WEBDAV = "webdav"
    SAMBA = "samba"


class Connection(Base, ResourceMixin, TimestampMixin):
    __table_args__ = (
        UniqueConstraint("name", "group_id"),
        Index("idx_connection_search_vector", "search_vector", postgresql_using="gin"),
    )

    type: Mapped[ConnectionType] = mapped_column(ChoiceType(ConnectionType, impl=String(32)), nullable=False)
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})

    group: Mapped[Group] = relationship("Group")

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

            -- === HOST FIELD (from JSON) ===
            -- Simple dictionary (no stemming) for exact match
            || to_tsvector('simple', coalesce(data->>'host', ''))
            -- Simple dictionary with translate(): split by . / - _ : \\ for partial token matching
            || to_tsvector(
                'simple',
                translate(coalesce(data->>'host', ''), './-_:\\', '      ')
            )
            """,
            persisted=True,
        ),
        nullable=False,
        deferred=True,
    )

    def __repr__(self):
        return f"<Connection name={self.name} description={self.description} group_id={self.group_id}>"
