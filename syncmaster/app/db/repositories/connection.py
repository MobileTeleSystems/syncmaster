from typing import Any, NoReturn

from sqlalchemy import ScalarResult, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Connection
from app.db.repositories.repository_with_owner import RepositoryWithOwner
from app.db.utils import Pagination
from app.exceptions import (
    ConnectionNotFound,
    ConnectionOwnerException,
    EntityNotFound,
    GroupNotFound,
    SyncmasterException,
    UserNotFound,
)


class ConnectionRepository(RepositoryWithOwner[Connection]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Connection, session=session)

    async def paginate(
        self,
        page: int,
        page_size: int,
        group_id: int,
    ) -> Pagination:
        stmt = select(Connection).where(
            Connection.is_deleted.is_(False),
            Connection.group_id == group_id,
        )

        return await self._paginate_scalar_result(
            query=stmt.order_by(Connection.name),
            page=page,
            page_size=page_size,
        )

    async def read_by_id(
        self,
        connection_id: int,
    ) -> Connection:
        stmt = select(Connection).where(Connection.id == connection_id, Connection.is_deleted.is_(False))
        result: ScalarResult[Connection] = await self._session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound as e:
            raise ConnectionNotFound from e

    async def create(
        self,
        group_id: int,
        name: str,
        description: str,
        data: dict[str, Any],
    ) -> Connection:
        query = (
            insert(Connection)
            .values(
                group_id=group_id,
                name=name,
                description=description,
                data=data,
            )
            .returning(Connection)
        )
        try:
            result: ScalarResult[Connection] = await self._session.scalars(query)
        except IntegrityError as e:
            self._raise_error(e)
        else:
            await self._session.flush()
            return result.one()

    async def update(
        self,
        connection_id: int,
        name: str | None,
        description: str | None,
        connection_data: dict[str, Any],
    ) -> Connection:
        try:
            connection = await self.read_by_id(connection_id=connection_id)
            for key in connection.data:
                if key not in connection_data or connection_data[key] is None:
                    connection_data[key] = connection.data[key]
            return await self._update(
                Connection.id == connection_id,
                Connection.is_deleted.is_(False),
                name=name or connection.name,
                description=description or connection.description,
                data=connection_data,
            )
        except IntegrityError as e:
            self._raise_error(e)

    async def delete(
        self,
        connection_id: int,
    ) -> None:
        try:
            await self._delete(connection_id)
        except (NoResultFound, EntityNotFound) as e:
            raise ConnectionNotFound from e

    async def copy(
        self,
        connection_id: int,
        new_group_id: int,
    ) -> Connection:
        try:
            kwargs_for_copy = dict(group_id=new_group_id)
            new_connection = await self._copy(
                Connection.id == connection_id,
                **kwargs_for_copy,
            )

            return new_connection

        except IntegrityError as integrity_error:
            self._raise_error(integrity_error)

    def _raise_error(self, err: DBAPIError) -> NoReturn:
        constraint = err.__cause__.__cause__.constraint_name  # type: ignore[union-attr]
        if constraint == "fk__connection__group_id__group":
            raise GroupNotFound from err
        if constraint == "fk__connection__user_id__user":
            raise UserNotFound from err
        if constraint == "ck__connection__owner_constraint":
            raise ConnectionOwnerException from err
        raise SyncmasterException from err
