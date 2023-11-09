from typing import Generic, TypeVar

from sqlalchemy import Select, and_, or_, select

from app.db.base import Base
from app.db.models import Group, UserGroup
from app.db.repositories.base import Repository

Model = TypeVar("Model", bound=Base)


class RepositoryWithOwner(Repository, Generic[Model]):
    def apply_user_permission(
        self,
        query: Select,
        user_id: int,
    ) -> Select:
        """Add to query filter access user to resource"""
        query = query.join(
            Group,
            Group.id == self._model.group_id,
            full=True,
        ).join(
            UserGroup,
            UserGroup.group_id == Group.id,
            full=True,
        )
        return query.where(
            or_(
                Group.admin_id == user_id,
                UserGroup.user_id == user_id,
            )
        ).group_by(self._model.id)

    async def check_admin_rights(
        self,
        user_id: int,
        group_id: int,
    ) -> bool:
        q = (
            select(Group)
            .where(
                Group.id == group_id,
                Group.admin_id == user_id,
            )
            .exists()
            .select()
        )

        return await self._session.scalar(q)

    async def check_user_rights(
        self,
        user_id: int,
        group_id: int,
    ) -> bool:
        q = (
            select(UserGroup)
            .join(
                Group,
                Group.id == UserGroup.group_id,
            )
            .where(
                or_(
                    and_(  # User in target group (exlude admin role)
                        UserGroup.group_id == group_id,
                        UserGroup.user_id == user_id,
                    ),
                    and_(  # User is a target group admin
                        Group.id == group_id,
                        Group.admin_id == user_id,
                    ),
                )
            )
            .exists()
            .select()
        )

        return await self._session.scalar(q)
