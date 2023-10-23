from __future__ import annotations

import enum
from datetime import datetime
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import ChoiceType

from app.db.base import Base
from app.db.mixins import DeletableMixin, ResourceMixin, TimestampMixin


class User(Base, TimestampMixin, DeletableMixin):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(256), nullable=False, unique=True, index=True
    )
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"User(username={self.username}, is_superuser={self.is_superuser}, is_active={self.is_active})"


class Group(Base, TimestampMixin, DeletableMixin):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    admin_id: Mapped[int] = mapped_column(
        ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True
    )

    admin: Mapped[User] = relationship("User")
    members: Mapped[list[User]] = relationship("User", secondary="user_group")

    def __repr__(self) -> str:
        return f"Group(name={self.name}, admin_id={self.admin_id})"


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


class Connection(Base, DeletableMixin, TimestampMixin, ResourceMixin):
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})
    auth_data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=True, default=None)
    queue_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("queue.id"), default=None
    )

    user: Mapped[User | None] = relationship("User")
    group: Mapped[Group | None] = relationship("Group")
    queue: Mapped[Queue | None] = relationship(
        "Queue",
        back_populates="connections",
    )

    def __repr__(self):
        return (
            f"<Connection "
            f"name={self.name} "
            f"description={self.description} "
            f"group_id={self.group_id} "
            f"user_id={self.user_id} "
            f"queue_id={self.queue_id}>"
        )


class Transfer(Base, DeletableMixin, TimestampMixin, ResourceMixin):
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
    strategy_params: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default={}
    )
    source_params: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default={}
    )
    target_params: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default={}
    )
    is_scheduled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    schedule: Mapped[str] = mapped_column(String(32), nullable=False, default="")

    user: Mapped[User | None] = relationship("User")
    group: Mapped[Group | None] = relationship("Group")
    source_connection: Mapped[Connection] = relationship(
        "Connection",
        foreign_keys=[source_connection_id],
    )
    target_connection: Mapped[Connection] = relationship(
        "Connection",
        foreign_keys=[target_connection_id],
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
    transfer_dump: Mapped[dict[str, Any]] = mapped_column(
        JSON, nullable=False, default={}
    )

    transfer: Mapped[Transfer] = relationship("Transfer")

    def __repr__(self):
        return (
            f"<Run"
            f" id={self.id}"
            f" transfer_id={self.transfer_id}"
            f" created_at={self.created_at:%Y-%m-%d %H:%M:%S}>"
        )


class ObjectType(enum.StrEnum):
    CONNECTION = "connection"
    TRANSFER = "transfer"
    QUEUE = "queue"


class Rule(enum.IntFlag):
    READ = 0
    WRITE = 1
    DELETE = 2

    @classmethod
    def from_str(cls, rule):
        if rule == "READ":
            return Rule.READ
        if rule == "WRITE":
            return Rule.WRITE
        if rule == "DELETE":
            return Rule.DELETE


class OwnerType(enum.StrEnum):
    GROUP = "group"
    USER = "user"


class Acl(Base):
    __table_args__ = (PrimaryKeyConstraint("object_id", "user_id", "object_type"),)
    object_id: Mapped[int] = mapped_column(
        BigInteger,
        nullable=False,
    )
    object_type: Mapped[ObjectType] = mapped_column(
        ChoiceType(ObjectType), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    rule: Mapped[Rule] = mapped_column(
        ChoiceType(Rule, impl=SmallInteger()), nullable=False, default=Rule.READ
    )


class Queue(Base, TimestampMixin, DeletableMixin):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(
        String(256),
        unique=True,
        nullable=False,
    )
    description: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    connections: Mapped[list[Connection]] = relationship(back_populates="queue")

    def __repr__(self):
        return f"<Queue name={self.name} description={self.description}>"
