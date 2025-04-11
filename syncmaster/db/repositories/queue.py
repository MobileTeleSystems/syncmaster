# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import NoReturn

from sqlalchemy import ScalarResult, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from syncmaster.db.models import Group, GroupMemberRole, Queue, User, UserGroup
from syncmaster.db.repositories.repository_with_owner import RepositoryWithOwner
from syncmaster.db.utils import Permission
from syncmaster.exceptions import EntityNotFoundError, SyncmasterError
from syncmaster.exceptions.group import GroupNotFoundError
from syncmaster.exceptions.queue import DuplicatedQueueNameError, QueueNotFoundError

# TODO: remove HTTP response schemes from repositories, these are different layers
from syncmaster.schemas.v1.queue import UpdateQueueSchema


class QueueRepository(RepositoryWithOwner[Queue]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Queue, session=session)

    async def create(self, queue_data: dict) -> Queue:
        query = insert(Queue).values(**queue_data).returning(Queue)
        try:
            result: ScalarResult[Queue] = await self._session.scalars(query)
        except IntegrityError as e:
            self._raise_error(e)
        else:
            await self._session.flush()
            return result.one()

    async def read_by_id(
        self,
        queue_id: int,
    ) -> Queue:
        stmt = (
            select(Queue)
            .where(Queue.id == queue_id)
            .options(selectinload(Queue.transfers))
            .options(selectinload(Queue.group))
        )
        try:
            result: ScalarResult[Queue] = await self._session.scalars(stmt)
            return result.one()
        except NoResultFound as e:
            raise QueueNotFoundError from e

    async def paginate(
        self,
        page: int,
        page_size: int,
        group_id: int,
        search_query: str | None = None,
    ):
        stmt = select(Queue).where(
            Queue.group_id == group_id,
        )
        if search_query:
            stmt = self._construct_vector_search(stmt, search_query)

        return await self._paginate_scalar_result(
            query=stmt.order_by(Queue.id),
            page=page,
            page_size=page_size,
        )

    async def update(
        self,
        queue_id: int,
        queue_data: UpdateQueueSchema,
    ) -> Queue:
        try:
            return await self._update(
                Queue.id == queue_id,
                name=queue_data.name,
                description=queue_data.description,
            )
        except IntegrityError as e:
            self._raise_error(e)

    async def delete(
        self,
        queue_id: int,
    ) -> None:
        try:
            await self._delete(queue_id)
        except (NoResultFound, EntityNotFoundError) as e:
            raise QueueNotFoundError from e

    async def get_group_permission(self, user: User, group_id: int) -> Permission:
        """
        Method for determining CRUD permissions in the specified group
        'DEVELOPER' does not have WRITE permission in the QUEUE repository
        """

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

        if group_role in (GroupMemberRole.Guest, GroupMemberRole.Developer):
            return Permission.READ

        return Permission.DELETE

    async def get_resource_permission(self, user: User, resource_id: int) -> Permission:  # noqa: WPS212
        """
        Method for determining CRUD rights in a repository (self.model) for a resource
        'DEVELOPER' does not have WRITE permission in the QUEUE repository
        """
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

        if group_role in (GroupMemberRole.Guest, GroupMemberRole.Developer):
            return Permission.READ

        return Permission.DELETE

    def _raise_error(self, err: DBAPIError) -> NoReturn:
        constraint = err.__cause__.__cause__.constraint_name
        if constraint == "uq__queue__slug":
            raise DuplicatedQueueNameError

        raise SyncmasterError from err
