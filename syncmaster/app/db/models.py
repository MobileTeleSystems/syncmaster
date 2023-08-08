import enum
from typing import Any

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    ForeignKey,
    PrimaryKeyConstraint,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship
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
    name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    description: Mapped[str] = mapped_column(String(512), nullable=False, default="")
    data: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False, default={})

    def __repr__(self):
        return (
            f"<Connection "
            f"name={self.name} "
            f"description={self.description} "
            f"group_id={self.group_id} "
            f"user_id={self.user_id}>"
        )

    @declared_attr  # type: ignore
    def __table_args__(cls) -> tuple:
        return (
            CheckConstraint(
                "(user_id IS NULL) <> (group_id IS NULL)", name="owner_constraint"
            ),
            UniqueConstraint("name", "user_id", "group_id"),
        )


class ObjectType(enum.StrEnum):
    CONNECTION = "connection"


class Rule(enum.IntFlag):
    READ = 0
    WRITE = 1
    DELETE = 2


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
