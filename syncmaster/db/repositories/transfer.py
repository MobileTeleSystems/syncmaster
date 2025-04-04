# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from typing import Any, NoReturn

from sqlalchemy import ScalarResult, insert, or_, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased, selectinload

from syncmaster.db.models import Connection, Transfer
from syncmaster.db.repositories.repository_with_owner import RepositoryWithOwner
from syncmaster.db.utils import Pagination
from syncmaster.exceptions import EntityNotFoundError, SyncmasterError
from syncmaster.exceptions.connection import ConnectionNotFoundError
from syncmaster.exceptions.group import GroupNotFoundError
from syncmaster.exceptions.queue import QueueNotFoundError
from syncmaster.exceptions.transfer import (
    DuplicatedTransferNameError,
    TransferNotFoundError,
    TransferOwnerError,
)
from syncmaster.exceptions.user import UserNotFoundError


class TransferRepository(RepositoryWithOwner[Transfer]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Transfer, session=session)

    async def paginate(
        self,
        page: int,
        page_size: int,
        group_id: int | None = None,
        search_query: str | None = None,
        source_connection_id: int | None = None,
        target_connection_id: int | None = None,
        queue_id: int | None = None,
        source_connection_type: list[str] | None = None,
        target_connection_type: list[str] | None = None,
        is_scheduled: bool | None = None,
    ) -> Pagination:
        stmt = select(Transfer).where(
            Transfer.group_id == group_id,
        )

        if search_query:
            processed_query = search_query.replace("/", " ").replace(".", " ")
            combined_query = f"{search_query} {processed_query}"
            stmt = self._construct_vector_search(stmt, combined_query)

        if source_connection_id is not None:
            stmt = stmt.where(Transfer.source_connection_id == source_connection_id)

        if target_connection_id is not None:
            stmt = stmt.where(Transfer.target_connection_id == target_connection_id)

        if queue_id is not None:
            stmt = stmt.where(Transfer.queue_id == queue_id)

        if is_scheduled is not None:
            stmt = stmt.where(Transfer.is_scheduled == is_scheduled)

        SourceConnection = aliased(Connection)
        TargetConnection = aliased(Connection)

        if source_connection_type is not None:
            stmt = stmt.join(
                SourceConnection,
                Transfer.source_connection_id == SourceConnection.id,
            )
            stmt = stmt.where(
                SourceConnection.type.in_(source_connection_type),
            )

        if target_connection_type is not None:
            stmt = stmt.join(
                TargetConnection,
                Transfer.target_connection_id == TargetConnection.id,
            )
            stmt = stmt.where(
                TargetConnection.type.in_(target_connection_type),
            )

        return await self._paginate_scalar_result(
            query=stmt.order_by(Transfer.name),
            page=page,
            page_size=page_size,
        )

    async def read_by_id(
        self,
        transfer_id: int,
    ) -> Transfer:
        stmt = (
            select(Transfer)
            .where(
                Transfer.id == transfer_id,
            )
            .options(selectinload(Transfer.queue))
        )
        try:
            result: ScalarResult[Transfer] = await self._session.scalars(stmt)
            return result.one()
        except NoResultFound as e:
            raise TransferNotFoundError from e

    async def create(
        self,
        group_id: int,
        source_connection_id: int,
        target_connection_id: int,
        name: str,
        description: str,
        source_params: dict[str, Any],
        target_params: dict[str, Any],
        strategy_params: dict[str, Any],
        transformations: list[dict[str, Any]],
        resources: dict[str, Any],
        queue_id: int,
        is_scheduled: bool,
        schedule: str | None,
    ) -> Transfer:
        query = (
            insert(Transfer)
            .values(
                group_id=group_id,
                source_connection_id=source_connection_id,
                target_connection_id=target_connection_id,
                name=name,
                description=description,
                source_params=source_params,
                target_params=target_params,
                strategy_params=strategy_params,
                transformations=transformations,
                resources=resources,
                queue_id=queue_id,
                is_scheduled=is_scheduled,
                schedule=schedule or "",
            )
            .returning(Transfer)
        )
        try:
            result: ScalarResult[Transfer] = await self._session.scalars(query)
        except IntegrityError as e:
            self._raise_error(e)
        else:
            await self._session.flush()
            return result.one()

    async def update(
        self,
        transfer_id: int,
        name: str,
        description: str,
        source_connection_id: int,
        target_connection_id: int,
        source_params: dict[str, Any],
        target_params: dict[str, Any],
        strategy_params: dict[str, Any],
        transformations: list[dict[str, Any]],
        resources: dict[str, Any],
        is_scheduled: bool,
        schedule: str | None,
        queue_id: int,
    ) -> Transfer:
        try:
            return await self._update(
                Transfer.id == transfer_id,
                name=name,
                description=description,
                strategy_params=strategy_params,
                is_scheduled=is_scheduled,
                schedule=schedule or "",
                source_connection_id=source_connection_id,
                target_connection_id=target_connection_id,
                source_params=source_params,
                target_params=target_params,
                transformations=transformations,
                resources=resources,
                queue_id=queue_id,
            )
        except IntegrityError as e:
            self._raise_error(e)

    async def delete(
        self,
        transfer_id: int,
    ) -> None:
        try:
            await self._delete(transfer_id)
        except (NoResultFound, EntityNotFoundError) as e:
            raise TransferNotFoundError from e

    async def copy(
        self,
        transfer_id: int,
        new_queue_id: int,
        new_group_id: int | None,
        new_source_connection: int | None,
        new_target_connection: int | None,
        new_name: str | None,
    ) -> Transfer:
        try:
            kwargs = dict(
                group_id=new_group_id,
                source_connection_id=new_source_connection,
                target_connection_id=new_target_connection,
                queue_id=new_queue_id,
                name=new_name,
            )
            new_transfer = await self._copy(Transfer.id == transfer_id, **kwargs)

            return new_transfer
        except IntegrityError as integrity_error:
            self._raise_error(integrity_error)

    async def list_by_connection_id(self, conn_id: int) -> Sequence[Transfer]:
        query = select(Transfer).where(
            or_(
                Transfer.source_connection_id == conn_id,
                Transfer.target_connection_id == conn_id,
            ),
        )
        result = await self._session.scalars(query)
        return result.fetchall()

    def _raise_error(self, err: DBAPIError) -> NoReturn:  # noqa: WPS238
        constraint = err.__cause__.__cause__.constraint_name
        if constraint == "fk__transfer__group_id__group":
            raise GroupNotFoundError from err
        if constraint == "fk__transfer__user_id__user":
            raise UserNotFoundError from err

        if constraint in [
            "fk__transfer__source_connection_id__connection",
            "fk__transfer__target_connection_id__connection",
        ]:
            raise ConnectionNotFoundError from err

        if constraint == "ck__transfer__owner_constraint":
            raise TransferOwnerError from err

        if constraint == "fk__transfer__queue_id__queue":
            raise QueueNotFoundError from err

        if constraint == "uq__transfer__name_group_id":
            raise DuplicatedTransferNameError

        raise SyncmasterError from err
