# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import enum
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, Computed, ForeignKey, PrimaryKeyConstraint, String
from sqlalchemy.dialects.postgresql import TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy_utils import ChoiceType

from syncmaster.db.mixins import TimestampMixin
from syncmaster.db.models.base import Base
from syncmaster.db.models.user import User

if TYPE_CHECKING:
    from syncmaster.db.models.queue import Queue


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


class Group(Base, TimestampMixin):
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    description: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    owner_id: Mapped[int] = mapped_column(ForeignKey("user.id", ondelete="CASCADE"), nullable=False, index=True)

    owner: Mapped[User] = relationship(User)
    queue: Mapped[Queue] = relationship(back_populates="group", cascade="all, delete-orphan")

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
    group: Mapped[Group] = relationship(viewonly=True)
