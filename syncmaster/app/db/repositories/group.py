import re
from typing import NoReturn

from sqlalchemy import ScalarResult, insert, or_, select, update
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Group, User, UserGroup
from app.db.repositories.base import Repository
from app.db.utils import Pagination, Permission
from app.exceptions import (
    AlreadyIsGroupMember,
    AlreadyIsNotGroupMember,
    EntityNotFound,
    GroupAdminNotFound,
    GroupAlreadyExists,
    GroupNotFound,
    SyncmasterException,
    UserNotFound,
)


class GroupRepository(Repository[Group]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Group, session=session)

    async def paginate_all(
        self,
        page: int,
        page_size: int,
    ) -> Pagination:
        stmt = select(Group).where(Group.is_deleted.is_(False))
        return await self._paginate_scalar_result(query=stmt.order_by(Group.name), page=page, page_size=page_size)

    async def paginate_for_user(
        self,
        page: int,
        page_size: int,
        current_user_id: int,
    ):
        stmt = (
            select(Group)
            .join(
                UserGroup,
                UserGroup.group_id == Group.id,
            )
            .where(
                Group.is_deleted.is_(False),
                or_(
                    UserGroup.user_id == current_user_id,
                    Group.admin_id == current_user_id,
                ),
            )
            .group_by(Group.id)
        )

        return await self._paginate_scalar_result(query=stmt.order_by(Group.name), page=page, page_size=page_size)

    async def read_by_id(
        self,
        group_id: int,
    ) -> Group:
        stmt = select(Group).where(Group.id == group_id, Group.is_deleted.is_(False))
        try:
            result: ScalarResult[Group] = await self._session.scalars(stmt)
            return result.one()
        except NoResultFound as e:
            raise GroupNotFound from e

    async def create(self, name: str, description: str, admin_id: int) -> Group:
        query = (
            insert(Group)
            .values(
                name=name,
                description=description,
                admin_id=admin_id,
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
        admin_id: int,
    ) -> Group:
        args = [Group.id == group_id, Group.is_deleted.is_(False)]
        try:
            return await self._update(
                *args,
                name=name,
                description=description,
                admin_id=admin_id,
            )
        except EntityNotFound as e:
            raise GroupNotFound from e
        except IntegrityError as e:
            self._raise_error(e)

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
                .returning(UserGroup)
            )
            await self._session.flush()
            obj = row_res.one_or_none()
        except IntegrityError as err:
            self._raise_error(err)

        if not obj:
            raise UserNotFound

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
                User.is_deleted.is_(False),
                User.is_active.is_(True),
                UserGroup.group_id == group.id,
            )
            .order_by(User.username)
        )
        return await self._paginate_raw_result(stmt, page=page, page_size=page_size)

    async def delete(self, group_id: int) -> None:
        try:
            await self._delete(group_id)
        except EntityNotFound as e:
            raise GroupNotFound from e

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
                )
            )
        except IntegrityError as integrity_error:
            self._raise_error(integrity_error)
        else:
            await self._session.flush()

    async def get_permission(self, user: User, group_id: int) -> Permission:
        # Check: group exists
        if not await self._session.get(Group, group_id):
            raise GroupNotFound

        admin_query = (
            (
                select(Group).where(
                    Group.admin_id == user.id,
                    Group.id == group_id,
                )
            )
            .exists()
            .select()
        )

        is_admin = await self._session.scalar(admin_query)

        if is_admin or user.is_superuser:
            return Permission.DELETE

        group_role_query = select(UserGroup).where(
            UserGroup.group_id == group_id,
            UserGroup.user_id == user.id,
        )

        user_group = await self._session.scalar(group_role_query)

        if not user_group:
            return Permission.NONE

        return Permission.READ

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
            raise AlreadyIsNotGroupMember
        await self._session.delete(user_group)
        await self._session.flush()

    def _raise_error(self, err: DBAPIError) -> NoReturn:
        constraint = err.__cause__.__cause__.constraint_name  # type: ignore[union-attr]

        if constraint == "fk__group__admin_id__user":
            raise GroupAdminNotFound from err

        if constraint == "uq__group__name":
            raise GroupAlreadyExists from err

        if constraint == "pk__user_group":
            raise AlreadyIsGroupMember from err

        if constraint == "fk__user_group__group_id__group":
            detail = err.__cause__.__cause__.detail  # type: ignore[union-attr]
            pattern = r'Key \(group_id\)=\(-?\d+\) is not present in table "group".'
            if re.match(pattern, detail):
                raise GroupNotFound from err

        if constraint == "fk__user_group__user_id__user":
            detail = err.__cause__.__cause__.detail  # type: ignore[union-attr]
            pattern = r'Key \(user_id\)=\(-?\d+\) is not present in table "user".'
            if re.match(pattern, detail):
                raise UserNotFound from err

        raise SyncmasterException from err
