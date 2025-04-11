# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import re
from typing import NoReturn

from sqlalchemy import ScalarResult, func, insert, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from syncmaster.db.models import Group, GroupMemberRole, User, UserGroup
from syncmaster.db.repositories.base import Repository
from syncmaster.db.utils import Pagination, Permission
from syncmaster.exceptions import EntityNotFoundError, SyncmasterError
from syncmaster.exceptions.group import (
    AlreadyIsGroupMemberError,
    AlreadyIsNotGroupMemberError,
    GroupAlreadyExistsError,
    GroupNotFoundError,
)
from syncmaster.exceptions.user import UserNotFoundError


class GroupRepository(Repository[Group]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Group, session=session)

    async def paginate_all(
        self,
        page: int,
        page_size: int,
        search_query: str | None = None,
    ) -> Pagination:
        stmt = select(Group)
        if search_query:
            stmt = self._construct_vector_search(stmt, search_query)

        paginated_result = await self._paginate_scalar_result(
            query=stmt.order_by(Group.name),
            page=page,
            page_size=page_size,
        )
        items = [{"data": group, "role": GroupMemberRole.Superuser} for group in paginated_result.items]

        return Pagination(
            items=items,
            total=paginated_result.total,
            page=page,
            page_size=page_size,
        )

    async def paginate_for_user(
        self,
        page: int,
        page_size: int,
        current_user_id: int,
        role: str | None = None,
        search_query: str | None = None,
    ) -> Pagination:
        roles_at_least = GroupMemberRole.roles_at_least(role) if role else None

        # if a role is specified and 'Owner' does not meet the required level, exclude owned groups
        if role and not GroupMemberRole.is_at_least_privilege_level(
            GroupMemberRole.Owner,
            role,
        ):
            owned_groups = []
            total_owned_groups = 0
        else:
            # query for groups where the user is the owner
            owned_groups_stmt = (
                select(Group)
                .where(
                    Group.owner_id == current_user_id,
                )
                .order_by(Group.name)
            )

            # apply search filtering if a search query is provided
            if search_query:
                owned_groups_stmt = self._construct_vector_search(owned_groups_stmt, search_query)

            # get total count of owned groups
            total_owned_groups = (
                await self._session.scalar(
                    select(func.count()).select_from(owned_groups_stmt.subquery()),
                )
                or 0
            )

            # fetch owned groups
            owned_groups_result = await self._session.execute(
                owned_groups_stmt,
            )
            owned_groups = [
                {"data": group, "role": GroupMemberRole.Owner.value} for group in owned_groups_result.scalars().all()
            ]

        #  query for groups where the user is a member (not Owner)
        user_groups_stmt = (
            select(UserGroup)
            .join(Group, UserGroup.group_id == Group.id)
            .where(
                UserGroup.user_id == current_user_id,
            )
            .order_by(Group.name)
        )

        # apply role-based filtering if a role is specified
        if roles_at_least:
            user_groups_stmt = user_groups_stmt.where(
                UserGroup.role.in_(roles_at_least),
            )

        # apply search filtering if a search query is provided
        if search_query:
            user_groups_stmt = self._construct_vector_search(user_groups_stmt, search_query)

        # get total count of user groups
        total_user_groups = (
            await self._session.scalar(
                select(func.count()).select_from(user_groups_stmt.subquery()),
            )
            or 0
        )

        user_groups_result = await self._session.execute(
            user_groups_stmt.options(joinedload(UserGroup.group)),
        )
        user_groups = [
            {"data": user_group.group, "role": user_group.role.value}
            for user_group in user_groups_result.scalars().all()
        ]

        # combine owned groups and user groups
        combined_groups = owned_groups + user_groups
        total_count = total_owned_groups + total_user_groups

        start = (page - 1) * page_size
        end = start + page_size
        paginated_items = combined_groups[start:end]

        return Pagination(
            items=paginated_items,
            total=total_count,
            page=page,
            page_size=page_size,
        )

    async def read_by_id(
        self,
        group_id: int,
    ) -> Group:
        stmt = select(Group).where(Group.id == group_id)
        try:
            result: ScalarResult[Group] = await self._session.scalars(stmt)
            return result.one()
        except NoResultFound as e:
            raise GroupNotFoundError from e

    async def create(self, name: str, description: str, owner_id: int) -> Group:
        query = (
            insert(Group)
            .values(
                name=name,
                description=description,
                owner_id=owner_id,
            )
            .returning(Group)
        )
        try:
            result: ScalarResult[Group] = await self._session.scalars(query)
            await self._session.flush()
        except IntegrityError as err:
            self._raise_error(err)
        else:
            return result.one()

    async def update(
        self,
        group_id: int,
        name: str,
        description: str,
        owner_id: int,
    ) -> Group:
        args = [Group.id == group_id]
        try:
            return await self._update(
                *args,
                name=name,
                description=description,
                owner_id=owner_id,
            )
        except EntityNotFoundError as e:
            raise GroupNotFoundError from e
        except IntegrityError as e:
            self._raise_error(e)

    async def get_member_role(self, group_id: int, user_id: int) -> GroupMemberRole:
        user_group = await self._session.get(
            UserGroup,
            {
                "group_id": group_id,
                "user_id": user_id,
            },
        )
        if user_group is None:  # then it's either the owner or a superuser because permission exists
            owner_query = (
                (
                    select(Group).where(
                        Group.owner_id == user_id,
                        Group.id == group_id,
                    )
                )
                .exists()
                .select()
            )
            is_owner = await self._session.scalar(owner_query)
            return GroupMemberRole.Owner if is_owner else GroupMemberRole.Superuser

        return user_group.role

    async def update_member_role(
        self,
        group_id: int,
        user_id: int,
        role: str,
    ):
        try:
            row_res = await self._session.scalars(
                update(UserGroup)
                .where(
                    UserGroup.group_id == group_id,
                    UserGroup.user_id == user_id,
                )
                .values(
                    group_id=group_id,
                    user_id=user_id,
                    role=role,
                )
                .returning(UserGroup),
            )
            await self._session.flush()
            obj = row_res.one_or_none()
        except IntegrityError as err:
            self._raise_error(err)

        if not obj:
            raise UserNotFoundError

        return obj

    async def get_member_paginate(
        self,
        page: int,
        page_size: int,
        group_id: int,
    ) -> Pagination:
        group = await self.read_by_id(group_id=group_id)
        stmt = (
            select(User, UserGroup.role)
            .join(
                UserGroup,
                UserGroup.user_id == User.id,
            )
            .where(
                User.is_active.is_(True),
                UserGroup.group_id == group.id,
            )
            .order_by(User.username)
        )
        return await self._paginate_raw_result(stmt, page=page, page_size=page_size)

    async def delete(self, group_id: int) -> None:
        try:
            await self._delete(group_id)
        except (EntityNotFoundError, NoResultFound) as e:
            raise GroupNotFoundError from e

    async def add_user(
        self,
        group_id: int,
        new_user_id: int,
        role: str,
    ) -> None:
        try:
            await self._session.execute(
                insert(UserGroup).values(
                    group_id=group_id,
                    user_id=new_user_id,
                    role=role,
                ),
            )
        except IntegrityError as integrity_error:
            self._raise_error(integrity_error)
        else:
            await self._session.flush()

    async def get_group_permission(self, user: User, group_id: int) -> Permission:
        """
        Method for determining CRUD rights in a specified group
        'DEVELOPER' and 'MAINTAINER' does not have WRITE and DELETE permission in the GROUP repository
        """
        # Check: group exists
        if not await self._session.get(Group, group_id):
            raise GroupNotFoundError

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

        if is_owner or user.is_superuser:
            return Permission.DELETE

        group_role_query = select(UserGroup).where(
            UserGroup.group_id == group_id,
            UserGroup.user_id == user.id,
        )

        user_group = await self._session.scalar(group_role_query)

        if not user_group:
            return Permission.NONE

        return Permission.READ

    async def get_user_group(self, group_id: int, user_id: int) -> UserGroup | None:
        return await self._session.get(
            UserGroup,
            {
                "group_id": group_id,
                "user_id": user_id,
            },
        )

    async def delete_user(
        self,
        group_id: int,
        target_user_id: int,
    ) -> None:
        user_group = await self._session.get(
            UserGroup,
            {
                "group_id": group_id,
                "user_id": target_user_id,
            },
        )
        if user_group is None:
            raise AlreadyIsNotGroupMemberError
        await self._session.delete(user_group)
        await self._session.flush()

    def _raise_error(self, err: DBAPIError) -> NoReturn:  # noqa: WPS238
        constraint = err.__cause__.__cause__.constraint_name

        if constraint == "fk__group__owner_id__user":
            raise UserNotFoundError from err

        if constraint == "uq__group__name":
            raise GroupAlreadyExistsError from err

        if constraint == "pk__user_group":
            raise AlreadyIsGroupMemberError from err

        if constraint == "fk__user_group__group_id__group":
            detail = err.__cause__.__cause__.detail
            pattern = r'Key \(group_id\)=\(-?\d+\) is not present in table "group".'
            if re.match(pattern, detail):
                raise GroupNotFoundError from err

        if constraint == "fk__user_group__user_id__user":
            detail = err.__cause__.__cause__.detail
            pattern = r'Key \(user_id\)=\(-?\d+\) is not present in table "user".'
            if re.match(pattern, detail):
                raise UserNotFoundError from err

        raise SyncmasterError from err
