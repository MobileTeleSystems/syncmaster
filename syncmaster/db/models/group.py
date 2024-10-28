# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Computed, ForeignKey, PrimaryKeyConstraint, String
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import ChoiceType

from syncmaster.db.mixins import DeletableMixin, TimestampMixin
from syncmaster.db.models.base import Base
from syncmaster.db.models.enums import GroupMemberRole
from syncmaster.db.models.user import User

if TYPE_CHECKING:
    from syncmaster.db.models.queue import Queue


class Group(Base, TimestampMixin, DeletableMixin):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)

    owner: Mapped[User] = relationship(User)
    members: Mapped[list[User]] = relationship(User, secondary="user_group")
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
