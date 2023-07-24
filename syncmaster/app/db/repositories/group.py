from typing import NoReturn

from sqlalchemy import ScalarResult, insert, or_, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Group, User, UserGroup
from app.db.repositories.base import Repository
from app.db.utils import Pagination
from app.exceptions import (
    ActionNotAllowed,
    AlreadyIsGroupMember,
    AlreadyIsNotGroupMember,
    EntityNotFound,
    GroupAdminNotFound,
    GroupAlreadyExists,
    SyncmasterException,
)


class GroupRepository(Repository[Group]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Group, session=session)

    async def paginate(
        self, page: int, page_size: int, current_user_id: int, is_superuser: bool
    ) -> Pagination:
        stmt = select(Group).where(Group.is_deleted.is_(False))
        if not is_superuser:
            stmt = stmt.join(
                UserGroup, UserGroup.group_id == Group.id, full=True
            ).where(
                or_(
                    UserGroup.user_id == current_user_id,
                    Group.admin_id == current_user_id,
                )
            )

        return await self._paginate(
            query=stmt.order_by(Group.name), page=page, page_size=page_size
        )

    async def read_by_id(
        self, group_id: int, is_superuser: bool, current_user_id: int
    ) -> Group:
        stmt = select(Group).where(Group.id == group_id, Group.is_deleted.is_(False))
        if not is_superuser:
            stmt = (
                stmt.join(UserGroup, UserGroup.group_id == Group.id, full=True)
                .where(
                    or_(
                        UserGroup.user_id == current_user_id,
                        Group.admin_id == current_user_id,
                    )
                )
                .distinct(Group.id)
            )
        result: ScalarResult[Group] = await self._session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound as e:
            raise EntityNotFound from e

    async def create(self, name: str, description: str, admin_id: int) -> Group:
        stmt = (
            insert(Group)
            .values(
                name=name,
                description=description,
                admin_id=admin_id,
            )
            .returning(Group)
        )
        try:
            result: ScalarResult[Group] = await self._session.scalars(
                select(Group).from_statement(stmt)
            )
            await self._session.commit()
        except IntegrityError as err:
            await self._session.rollback()
            self._raise_error(err)
        else:
            return result.one()

    async def update(
        self,
        group_id: int,
        current_user_id: int,
        is_superuser: bool,
        name: str,
        description: str,
        admin_id: int,
    ) -> Group:
        args = [Group.id == group_id]
        if not is_superuser:
            args.append(Group.admin_id == current_user_id)
        try:
            return await self._update(
                *args, name=name, description=description, admin_id=admin_id
            )
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)

    async def get_member_paginate(
        self,
        page: int,
        page_size: int,
        group_id: int,
        current_user_id: int,
        is_superuser: bool,
    ) -> Pagination:
        group = await self.read_by_id(
            group_id=group_id,
            is_superuser=is_superuser,
            current_user_id=current_user_id,
        )
        stmt = (
            select(User)
            .join(UserGroup, UserGroup.user_id == User.id)
            .where(
                User.is_deleted.is_(False),
                User.is_active.is_(True),
                UserGroup.group_id == group.id,
            )
            .order_by(User.username)
        )
        return await self._paginate(stmt, page=page, page_size=page_size)

    async def delete(self, group_id: int) -> None:
        await self._delete(group_id)

    async def add_user(
        self,
        group_id: int,
        target_user_id: int,
        current_user_id: int,
        is_superuser: bool,
    ) -> None:
        group = await self.read_by_id(
            group_id=group_id,
            is_superuser=is_superuser,
            current_user_id=current_user_id,
        )
        if not (group.admin_id == current_user_id or is_superuser):
            raise ActionNotAllowed
        try:
            await self._session.execute(
                insert(UserGroup).values(group_id=group_id, user_id=target_user_id)
            )
        except IntegrityError as err:
            await self._session.rollback()
            self._raise_error(err)
        else:
            await self._session.commit()

    async def delete_user(
        self,
        group_id: int,
        target_user_id: int,
        current_user_id: int,
        is_superuser: bool,
    ) -> None:
        group = await self.read_by_id(
            group_id=group_id,
            is_superuser=is_superuser,
            current_user_id=current_user_id,
        )
        if not (
            group.admin_id == current_user_id
            or is_superuser
            or target_user_id == current_user_id
        ):
            raise ActionNotAllowed

        ug = await self._session.get(
            UserGroup,
            {
                "group_id": group_id,
                "user_id": target_user_id,
            },
        )
        if ug is None:
            raise AlreadyIsNotGroupMember
        await self._session.delete(ug)
        await self._session.commit()

    def _raise_error(self, err: DBAPIError) -> NoReturn:
        constraint = err.__cause__.__cause__.constraint_name  # type: ignore
        if constraint == "fk__group__admin_id__user":
            raise GroupAdminNotFound from err
        if constraint == "uq__group__name":
            raise GroupAlreadyExists

        if constraint == "pk__user_group":
            raise AlreadyIsGroupMember
        raise SyncmasterException from err
