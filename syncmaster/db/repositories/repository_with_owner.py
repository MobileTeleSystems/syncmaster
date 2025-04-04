# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Generic, TypeVar

from sqlalchemy import select

from syncmaster.db.models import Base, Group, GroupMemberRole, User, UserGroup
from syncmaster.db.repositories.base import Repository
from syncmaster.db.utils import Permission
from syncmaster.exceptions.group import GroupNotFoundError

Model = TypeVar("Model", bound=Base)


class RepositoryWithOwner(Repository, Generic[Model]):
    async def get_resource_permission(self, user: User, resource_id: int) -> Permission:  # noqa: WPS212
        """Method for determining CRUD rights in a repository (self.model) for a resource"""
        is_exists = await self._session.get(self._model, resource_id)

        if not is_exists:
            return Permission.NONE

        if user.is_superuser:
            return Permission.DELETE

        owner_query = (
            (
                select(self._model)
                .join(
                    Group,
                    Group.id == self._model.group_id,
                )
                .where(
                    Group.owner_id == user.id,
                    self._model.id == resource_id,
                )
            )
            .exists()
            .select()
        )

        is_owner = await self._session.scalar(owner_query)

        if is_owner:
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

        if group_role == GroupMemberRole.Developer:
            return Permission.WRITE

        return Permission.DELETE  # Maintainer

    async def get_group_permission(self, user: User, group_id: int) -> Permission:  # noqa: WPS212
        """Method for determining CRUD permissions in the specified group"""
        owner_query = (
            (
                select(Group).where(
                    Group.owner_id == user.id,
                    Group.id == group_id,
                )
            )
            .exists()
            .select()
        )

        is_owner = await self._session.scalar(owner_query)

        if is_owner:
            return Permission.DELETE

        group_role_query = select(UserGroup).where(
            UserGroup.group_id == group_id,
            UserGroup.user_id == user.id,
        )

        user_group = await self._session.scalar(group_role_query)

        if not user_group:
            # Check: group exists
            if not await self._session.get(Group, group_id):
                raise GroupNotFoundError

            # If the user is not in the group, then he is either a superuser or does not have any rights
            if not user.is_superuser:
                return Permission.NONE
            else:
                return Permission.DELETE

        group_role = user_group.role

        if group_role == GroupMemberRole.Guest:
            return Permission.READ

        if group_role == GroupMemberRole.Developer:
            return Permission.WRITE

        return Permission.DELETE  # Maintainer
