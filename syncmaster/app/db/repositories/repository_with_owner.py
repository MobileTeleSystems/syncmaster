from typing import Generic, TypeVar

from sqlalchemy import select

from app.db.base import Base
from app.db.models import Group, GroupMemberRole, User, UserGroup
from app.db.repositories.base import Repository
from app.db.utils import Permission

Model = TypeVar("Model", bound=Base)


class RepositoryWithOwner(Repository, Generic[Model]):
    async def get_permission(self, user: User, resource_id: int) -> Permission:
        if user.is_superuser:
            return Permission.DELETE

        admin_query = (
            (
                select(self._model)
                .join(
                    Group,
                    Group.id == self._model.group_id,
                )
                .where(
                    Group.admin_id == user.id,
                    self._model.id == resource_id,
                )
            )
            .exists()
            .select()
        )

        is_admin = await self._session.scalar(admin_query)

        if is_admin:
            return Permission.DELETE

        group_role_query = (
            select(UserGroup)
            .join(
                self._model,
                UserGroup.group_id == self._model.group_id,
            )
            .where(self._model.id == resource_id, UserGroup.user_id == user.id)
        )

        user_group = await self._session.scalar(group_role_query)

        if not user_group:
            return Permission.NONE

        group_role = user_group.role

        if group_role == GroupMemberRole.Guest:
            return Permission.READ

        if group_role == GroupMemberRole.User:
            return Permission.WRITE

        return Permission.DELETE  # Maintainer
