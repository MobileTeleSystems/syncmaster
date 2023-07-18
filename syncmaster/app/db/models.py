from sqlalchemy import BigInteger, Boolean, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import DeletableMixin, TimestampMixin


class User(Base, TimestampMixin, DeletableMixin):
    __table_args__ = (Index(None, "id", "is_deleted", "is_active"),)
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(256), nullable=False, unique=True, index=True
    )
    is_superuser: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    def __repr__(self) -> str:
        return f"User(username={self.username}, is_superuser={self.is_superuser}, is_active={self.is_active})"
