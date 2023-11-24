from collections.abc import Sequence
from typing import Any, NoReturn

from sqlalchemy import ScalarResult, insert, or_, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Transfer
from app.db.repositories.repository_with_owner import RepositoryWithOwner
from app.db.utils import Pagination
from app.exceptions import (
    ConnectionNotFound,
    EntityNotFound,
    GroupNotFound,
    SyncmasterException,
    TransferNotFound,
    TransferOwnerException,
    UserNotFound,
)


class TransferRepository(RepositoryWithOwner[Transfer]):
    def __init__(self, session: AsyncSession):
        super().__init__(model=Transfer, session=session)

    async def paginate(
        self,
        page: int,
        page_size: int,
        group_id: int | None = None,
    ) -> Pagination:
        stmt = select(Transfer).where(Transfer.is_deleted.is_(False))

        return await self._paginate_scalar_result(
            query=stmt.where(Transfer.group_id == group_id).order_by(Transfer.name),
            page=page,
            page_size=page_size,
        )

    async def read_by_id(
        self,
        transfer_id: int,
    ) -> Transfer:
        stmt = select(Transfer).where(
            Transfer.id == transfer_id,
            Transfer.is_deleted.is_(False),
        )
        try:
            result: ScalarResult[Transfer] = await self._session.scalars(stmt)
            return result.one()
        except NoResultFound as e:
            raise TransferNotFound from e

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
        queue_id: int,
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
                queue_id=queue_id,
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
        transfer: Transfer,
        name: str | None,
        description: str | None,
        source_connection_id: int | None,
        target_connection_id: int | None,
        source_params: dict[str, Any],
        target_params: dict[str, Any],
        strategy_params: dict[str, Any],
        is_scheduled: bool | None,
        schedule: str | None,
    ) -> Transfer:
        try:
            for key in transfer.source_params:
                if key not in source_params or source_params[key] is None:
                    source_params[key] = transfer.source_params[key]
            for key in transfer.target_params:
                if key not in target_params or target_params[key] is None:
                    target_params[key] = transfer.target_params[key]
            for key in transfer.strategy_params:
                if key not in strategy_params or strategy_params[key] is None:
                    strategy_params[key] = transfer.strategy_params[key]
            return await self._update(
                Transfer.id == transfer.id,
                Transfer.is_deleted.is_(False),
                name=name or transfer.name,
                description=description or transfer.description,
                strategy_params=strategy_params,
                is_scheduled=is_scheduled or transfer.is_scheduled,
                schedule=schedule or transfer.schedule,
                source_connection_id=source_connection_id or transfer.source_connection_id,
                target_connection_id=target_connection_id or transfer.target_connection_id,
                source_params=source_params,
                target_params=target_params,
            )
        except IntegrityError as e:
            self._raise_error(e)

    async def delete(
        self,
        transfer_id: int,
    ) -> None:
        try:
            await self._delete(transfer_id)
        except (NoResultFound, EntityNotFound) as e:
            raise TransferNotFound from e

    async def copy(
        self,
        transfer_id: int,
        new_queue_id: int,
        new_group_id: int | None,
        new_source_connection: int | None,
        new_target_connection: int | None,
    ) -> Transfer:
        try:
            kwargs = dict(
                group_id=new_group_id,
                source_connection_id=new_source_connection,
                target_connection_id=new_target_connection,
                queue_id=new_queue_id,
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
            )
        )
        result = await self._session.scalars(query)
        return result.fetchall()

    def _raise_error(self, err: DBAPIError) -> NoReturn:
        constraint = err.__cause__.__cause__.constraint_name  # type: ignore[union-attr]
        if constraint == "fk__transfer__group_id__group":
            raise GroupNotFound from err
        if constraint == "fk__transfer__user_id__user":
            raise UserNotFound from err

        if constraint in [
            "fk__transfer__source_connection_id__connection",
            "fk__transfer__target_connection_id__connection",
        ]:
            raise ConnectionNotFound from err

        if constraint == "ck__transfer__owner_constraint":
            raise TransferOwnerException from err
        raise SyncmasterException from err
