from datetime import datetime

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, declared_attr, mapped_column


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        server_onupdate=func.now(),  # type: ignore
        onupdate=datetime.now,
        nullable=False,
    )


class DeletableMixin:
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)


class ResourceMixin:
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    group_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey("group.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    description: Mapped[str] = mapped_column(String(512), nullable=False, default="")

    @declared_attr  # type: ignore
    def __table_args__(cls) -> tuple:
        return (
            CheckConstraint(
                "(user_id IS NULL) <> (group_id IS NULL)", name="owner_constraint"
            ),
            UniqueConstraint("name", "user_id", "group_id"),
        )
