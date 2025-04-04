# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from typing import Any, NoReturn

from sqlalchemy import ScalarResult, insert, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection
from syncmaster.db.repositories.repository_with_owner import RepositoryWithOwner
from syncmaster.db.utils import Pagination
from syncmaster.exceptions import EntityNotFoundError, SyncmasterError
from syncmaster.exceptions.connection import (
    ConnectionNotFoundError,
    ConnectionOwnerError,
    DuplicatedConnectionNameError,
)
from syncmaster.exceptions.group import GroupNotFoundError
from syncmaster.exceptions.user import UserNotFoundError


class ConnectionRepository(RepositoryWithOwner[Connection]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Connection, session=session)

    async def paginate(
        self,
        page: int,
        page_size: int,
        group_id: int,
        search_query: str | None = None,
        connection_type: list[str] | None = None,
    ) -> Pagination:
        stmt = select(Connection).where(
            Connection.group_id == group_id,
        )
        if search_query:
            processed_query = search_query.replace(".", " ")
            combined_query = f"{search_query} {processed_query}"
            stmt = self._construct_vector_search(stmt, combined_query)

        if connection_type is not None:
            stmt = stmt.where(Connection.type.in_(connection_type))

        return await self._paginate_scalar_result(
            query=stmt.order_by(Connection.name),
            page=page,
            page_size=page_size,
        )

    async def read_by_id(
        self,
        connection_id: int,
    ) -> Connection:
        stmt = select(Connection).where(Connection.id == connection_id)
        result: ScalarResult[Connection] = await self._session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound as e:
            raise ConnectionNotFoundError from e

    async def create(
        self,
        group_id: int,
        type: str,
        name: str,
        description: str,
        data: dict[str, Any],
    ) -> Connection:
        query = (
            insert(Connection)
            .values(
                group_id=group_id,
                type=type,
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
        name: str,
        type: str,
        description: str,
        data: dict[str, Any],
    ) -> Connection:
        try:
            return await self._update(
                Connection.id == connection_id,
                type=type,
                name=name,
                description=description,
                data=data,
            )
        except IntegrityError as e:
            self._raise_error(e)

    async def delete(
        self,
        connection_id: int,
    ) -> None:
        try:
            await self._delete(connection_id)
        except (NoResultFound, EntityNotFoundError) as e:
            raise ConnectionNotFoundError from e

    async def copy(
        self,
        connection_id: int,
        new_group_id: int,
        new_name: str | None,
    ) -> Connection:
        try:
            kwargs_for_copy = dict(group_id=new_group_id, name=new_name)
            new_connection = await self._copy(
                Connection.id == connection_id,
                **kwargs_for_copy,
            )

            return new_connection

        except IntegrityError as integrity_error:
            self._raise_error(integrity_error)

    def _raise_error(self, err: DBAPIError) -> NoReturn:  # noqa: WPS238
        constraint = err.__cause__.__cause__.constraint_name
        if constraint == "fk__connection__group_id__group":
            raise GroupNotFoundError from err
        if constraint == "fk__connection__user_id__user":
            raise UserNotFoundError from err
        if constraint == "ck__connection__owner_constraint":
            raise ConnectionOwnerError from err
        if constraint == "uq__connection__name_group_id":
            raise DuplicatedConnectionNameError from err
        raise SyncmasterError from err
