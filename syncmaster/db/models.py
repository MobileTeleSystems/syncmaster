# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    Computed,
    DateTime,
    ForeignKey,
    Index,
    PrimaryKeyConstraint,
    String,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
from sqlalchemy_utils import ChoiceType

from syncmaster.db.base import Base
from syncmaster.db.mixins import DeletableMixin, ResourceMixin, TimestampMixin


class GroupMemberRole(enum.StrEnum):
    Maintainer = "Maintainer"
    Developer = "Developer"
    Owner = "Owner"
    Guest = "Guest"
    Superuser = "Superuser"

    @classmethod
    def public_roles(cls) -> list[GroupMemberRole]:
        return [cls.Maintainer, cls.Developer, cls.Guest]

    @classmethod
    def public_roles_str(cls) -> str:
        return ", ".join([role.value for role in cls.public_roles()])

    @classmethod
    def is_public_role(cls, role: str) -> bool:
        try:
            role_enum = cls(role)
            return role_enum in cls.public_roles()
        except ValueError:
            return False

    @classmethod
    def role_hierarchy(cls) -> dict[GroupMemberRole, int]:
        return {
            cls.Guest: 1,
            cls.Developer: 2,
            cls.Maintainer: 3,
            cls.Owner: 4,
            cls.Superuser: 5,
        }

    @classmethod
    def is_at_least_privilege_level(
        cls,
        role1: str | GroupMemberRole,
        role2: str | GroupMemberRole,
    ) -> bool:
        role1_enum = cls(role1) if isinstance(role1, str) else role1
        role2_enum = cls(role2) if isinstance(role2, str) else role2
        hierarchy = cls.role_hierarchy()
        return hierarchy.get(role1_enum, 0) >= hierarchy.get(role2_enum, 0)

    @classmethod
    def roles_at_least(cls, role: str | GroupMemberRole) -> list[str]:
        role_enum = cls(role) if isinstance(role, str) else role
        required_level = cls.role_hierarchy()[role_enum]
        return [r.value for r, level in cls.role_hierarchy().items() if level >= required_level]


class User(Base, TimestampMixin, DeletableMixin):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(String(256), nullable=False, unique=True, index=True)
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"User(username={self.username}, is_superuser={self.is_superuser}, is_active={self.is_active})"


class Group(Base, TimestampMixin, DeletableMixin):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)

    owner: Mapped[User] = relationship("User")
    members: Mapped[list[User]] = relationship("User", secondary="user_group")
    queue: Mapped[Queue] = relationship(back_populates="group")

    search_vector: Mapped[str] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english'::regconfig, name)", persisted=True),
        nullable=False,
        deferred=True,
        doc="Full-text search vector",
    )

    def __repr__(self) -> str:
        return f"Group(name={self.name}, owner_id={self.owner_id})"


class UserGroup(Base):
    __table_args__ = (PrimaryKeyConstraint("user_id", "group_id"),)
    user_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    group_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("group.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[GroupMemberRole] = mapped_column(
        ChoiceType(GroupMemberRole),
        nullable=False,
    )
    group: Mapped[Group] = relationship("Group")


class Connection(Base, ResourceMixin, DeletableMixin, TimestampMixin):
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})

    group: Mapped[Group] = relationship("Group")

    def __repr__(self):
        return f"<Connection " f"name={self.name} " f"description={self.description} " f"group_id={self.group_id}>"

    @declared_attr
    def __table_args__(cls) -> tuple:
        return (UniqueConstraint("name", "group_id"),)


class AuthData(Base, TimestampMixin):
    connection_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("connection.id", ondelete="CASCADE"),
        primary_key=True,
    )
    value: Mapped[str] = mapped_column(nullable=False)


class Transfer(
    Base,
    ResourceMixin,
    DeletableMixin,
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
    is_scheduled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    schedule: Mapped[str] = mapped_column(String(32), nullable=False, default="")
    queue_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("queue.id", ondelete="CASCADE"),
        nullable=False,
    )

    group: Mapped[Group] = relationship("Group")
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


class Status(enum.StrEnum):
    CREATED = "CREATED"
    STARTED = "STARTED"
    FAILED = "FAILED"
    SEND_STOP_SIGNAL = "SEND_STOP_SIGNAL"
    STOPPED = "STOPPED"
    FINISHED = "FINISHED"


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
        DateTime,
        nullable=True,
        default=None,
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=None,
    )
    status: Mapped[Status] = mapped_column(
        ChoiceType(Status),
        nullable=False,
        default=Status.CREATED,
        index=True,
    )
    log_url: Mapped[str] = mapped_column(String(512), nullable=True)
    transfer_dump: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})

    transfer: Mapped[Transfer] = relationship("Transfer")

    def __repr__(self):
        return (
            f"<Run "
            f"id={self.id} "
            f"transfer_id={self.transfer_id} "
            f"created_at={self.created_at:%Y-%m-%d %H:%M:%S}>"
        )


class Queue(Base, ResourceMixin, TimestampMixin, DeletableMixin):
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)

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
        return f"<Queue name={self.name} description={self.description}>"
