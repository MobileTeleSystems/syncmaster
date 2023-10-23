from typing import NoReturn

from sqlalchemy import ScalarResult, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import ObjectType, Queue
from app.db.repositories.base import RepositoryWithAcl
from app.exceptions import QueueNotFound, SyncmasterException
from app.exceptions.base import EntityNotFound


class QueueRepository(RepositoryWithAcl[Queue]):
    def __init__(self, session: AsyncSession):
        self._object_type = ObjectType.QUEUE
        super().__init__(model=Queue, session=session)

    async def create(
        self,
        name: str,
        description: str | None,
        is_active: bool,
    ) -> Queue:
        query = (
            insert(Queue)
            .values(
                name=name,
                description=description,
                is_active=is_active,
            )
            .returning(Queue)
        )
        try:
            result: ScalarResult[Queue] = await self._session.scalars(query)
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)
        else:
            await self._session.commit()
            return result.one()

    async def read_by_id(
        self,
        queue_id: int,
    ) -> Queue:
        stmt = (
            select(Queue)
            .where(Queue.id == queue_id, Queue.is_deleted.is_(False))
            .options(selectinload(Queue.connections))
        )
        result: ScalarResult[Queue] = await self._session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound as e:
            raise QueueNotFound from e

    async def paginate(
        self,
        page: int,
        page_size: int,
    ):
        stmt = select(Queue).where(Queue.is_deleted.is_(False))
        return await self._paginate(
            query=stmt.order_by(Queue.name),
            page=page,
            page_size=page_size,
        )

    async def update(
        self,
        queue_id: int,
        name: str | None,
        description: str | None,
        is_active: bool | None,
    ) -> Queue:
        try:
            queue = await self.read_by_id(
                queue_id=queue_id,
            )
            return await self._update(
                Queue.id == queue_id,
                Queue.is_deleted.is_(False),
                name=name or queue.name,
                description=description or queue.description,
                is_active=is_active if is_active is not None else queue.is_active,
            )
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)

    async def delete(
        self,
        queue_id: int,
    ) -> None:
        try:
            await self._delete(queue_id)
        except (NoResultFound, EntityNotFound) as e:
            raise QueueNotFound from e

    @staticmethod
    def _raise_error(err: DBAPIError) -> NoReturn:
        raise SyncmasterException from err
