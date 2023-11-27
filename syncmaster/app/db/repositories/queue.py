from typing import NoReturn

from sqlalchemy import ScalarResult, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.v1.queue.schemas import UpdateQueueSchema
from app.db.models import Group, GroupMemberRole, Queue, User, UserGroup
from app.db.repositories.repository_with_owner import RepositoryWithOwner
from app.db.utils import Permission
from app.exceptions import EntityNotFoundError, GroupNotFoundError, SyncmasterError
from app.exceptions.queue import QueueNotFoundError


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
            .where(Queue.id == queue_id, Queue.is_deleted.is_(False))
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
    ):
        stmt = select(Queue).where(
            Queue.is_deleted.is_(False),
            Queue.group_id == group_id,
        )
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
            queue = await self.read_by_id(queue_id=queue_id)
            return await self._update(
                Queue.id == queue_id,
                Queue.is_deleted.is_(False),
                description=queue_data.description or queue.description,
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
        'User' does not have WRITE permission in the QUEUE repository
        """

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

        if is_admin:
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

        if group_role in (GroupMemberRole.Guest, GroupMemberRole.User):
            return Permission.READ

        return Permission.DELETE

    async def get_resource_permission(self, user: User, resource_id: int) -> Permission:
        """
        Method for determining CRUD rights in a repository (self.model) for a resource
        'User' does not have WRITE permission in the QUEUE repository
        """
        is_exists = await self._session.get(self._model, resource_id)

        if not is_exists:
            return Permission.NONE

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

        if group_role in (GroupMemberRole.Guest, GroupMemberRole.User):
            return Permission.READ

        return Permission.DELETE

    @staticmethod
    def _raise_error(err: DBAPIError) -> NoReturn:
        raise SyncmasterError from err
