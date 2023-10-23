from collections.abc import Sequence
from typing import Any, NoReturn

from sqlalchemy import ScalarResult, insert, or_, select
from sqlalchemy.exc import DBAPIError, IntegrityError, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import Acl, Connection, ObjectType, Rule, Transfer
from app.db.repositories.base import RepositoryWithAcl
from app.db.utils import Pagination
from app.exceptions import (
    AclNotFound,
    ActionNotAllowed,
    ConnectionNotFound,
    EntityNotFound,
    GroupNotFound,
    SyncmasterException,
    TransferNotFound,
    TransferOwnerException,
    UserNotFound,
)


class TransferRepository(RepositoryWithAcl[Transfer]):
    def __init__(self, session: AsyncSession):
        self._object_type = ObjectType.TRANSFER
        super().__init__(model=Transfer, session=session)

    async def paginate(
        self,
        page: int,
        page_size: int,
        current_user_id: int,
        is_superuser: bool,
        group_id: int | None = None,
        user_id: int | None = None,
    ) -> Pagination:
        if not is_superuser and user_id and current_user_id != user_id:
            raise ActionNotAllowed
        stmt = select(Transfer).where(Transfer.is_deleted.is_(False))
        args = []
        if user_id is not None:
            args.append(Transfer.user_id == user_id)
        if group_id is not None:
            args.append(Transfer.group_id == group_id)

        if not is_superuser:
            stmt = self.apply_acl(stmt, current_user_id)
        return await self._paginate(
            query=stmt.where(*args).order_by(Transfer.name),
            page=page,
            page_size=page_size,
        )

    async def read_by_id(
        self,
        transfer_id: int,
        current_user_id: int,
        is_superuser: bool,
        rule: Rule = Rule.READ,
    ) -> Transfer:
        stmt = (
            select(Transfer)
            .where(
                Transfer.id == transfer_id,
                Transfer.is_deleted.is_(False),
            )
            .options(
                selectinload(Transfer.source_connection).selectinload(Connection.queue)
            )
            .options(
                selectinload(Transfer.target_connection).selectinload(Connection.queue)
            )
        )
        if not is_superuser:
            stmt = self.apply_acl(stmt, current_user_id, rule=rule)
        result: ScalarResult[Transfer] = await self._session.scalars(stmt)
        try:
            return result.one()
        except NoResultFound as e:
            raise TransferNotFound from e

    async def create(
        self,
        user_id: int | None,
        group_id: int | None,
        source_connection_id: int,
        target_connection_id: int,
        name: str,
        description: str,
        source_params: dict[str, Any],
        target_params: dict[str, Any],
        strategy_params: dict[str, Any],
    ) -> Transfer:
        query = (
            insert(Transfer)
            .values(
                user_id=user_id,
                group_id=group_id,
                source_connection_id=source_connection_id,
                target_connection_id=target_connection_id,
                name=name,
                description=description,
                source_params=source_params,
                target_params=target_params,
                strategy_params=strategy_params,
            )
            .returning(Transfer)
        )
        try:
            result: ScalarResult[Transfer] = await self._session.scalars(query)
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)
        else:
            await self._session.commit()
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
                source_connection_id=source_connection_id
                or transfer.source_connection_id,
                target_connection_id=target_connection_id
                or transfer.target_connection_id,
                source_params=source_params,
                target_params=target_params,
            )
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)

    async def delete(
        self, transfer_id: int, current_user_id: int, is_superuser: bool
    ) -> None:
        if not is_superuser:
            await self.read_by_id(
                transfer_id=transfer_id,
                current_user_id=current_user_id,
                is_superuser=False,
                rule=Rule.DELETE,
            )
        try:
            await self._delete(transfer_id)
        except (NoResultFound, EntityNotFound) as e:
            raise TransferNotFound from e

    async def add_or_update_rule(
        self,
        transfer_id: int,
        current_user_id: int,
        is_superuser: bool,
        rule: Rule,
        target_user_id: int,
    ) -> Acl:
        if not is_superuser and not await self.has_owner_access(
            object_id=transfer_id,
            user_id=current_user_id,
        ):
            raise TransferNotFound
        transfer = await self.read_by_id(
            transfer_id=transfer_id,
            current_user_id=current_user_id,
            is_superuser=is_superuser,
        )
        if transfer.group_id is None:
            raise ActionNotAllowed
        try:
            return await self._add_or_update_rule(
                object_id=transfer_id,
                user_id=target_user_id,
                rule=rule,
            )
        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)

    async def delete_rule(
        self,
        current_user_id: int,
        is_superuser: bool,
        transfer_id: int,
        target_user_id: int,
    ):
        if not is_superuser and not await self.has_owner_access(
            object_id=transfer_id,
            user_id=current_user_id,
        ):
            raise TransferNotFound
        transfer = await self.read_by_id(
            transfer_id=transfer_id,
            current_user_id=current_user_id,
            is_superuser=is_superuser,
        )
        if transfer.group_id is None:
            raise ActionNotAllowed
        try:
            await self._delete_acl_rule(
                object_id=transfer_id,
                user_id=target_user_id,
            )
        except EntityNotFound as e:
            raise AclNotFound from e
        return

    async def copy_transfer(
        self,
        transfer_id: int,
        new_group_id: int | None,
        new_user_id: int | None,
        new_source_connection: int | None,
        new_target_connection: int | None,
        remove_source: bool,
        is_superuser: bool,
        current_user_id,
    ) -> Transfer:
        if not is_superuser:
            if not await self.has_owner_access(
                transfer_id,
                current_user_id,
            ):
                raise TransferNotFound

        try:
            kwargs = dict(
                user_id=new_user_id,
                group_id=new_group_id,
                source_connection_id=new_source_connection,
                target_connection_id=new_target_connection,
            )
            new_transfer = await self._copy(Transfer.id == transfer_id, **kwargs)

            if remove_source:
                await self._delete(transfer_id)

            return new_transfer

        except IntegrityError as e:
            await self._session.rollback()
            self._raise_error(e)

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
