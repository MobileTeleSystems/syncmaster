from typing import Any, NoReturn

from sqlalchemy import desc, select
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.api.v1.transfers.schemas import ReadFullTransferSchema
from app.db.models import Run, Status, Transfer
from app.db.repositories.base import Repository
from app.db.utils import Pagination
from app.exceptions import (
    CannotStopRunException,
    RunNotFoundException,
    SyncmasterException,
    TransferNotFound,
)


class RunRepository(Repository[Run]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Run, session=session)

    async def paginate(
        self,
        transfer_id: int,
        page: int,
        page_size: int,
    ) -> Pagination:
        query = (
            select(Run)
            .where(Run.transfer_id == transfer_id)
            .order_by(desc(Run.created_at))
        )
        return await self._paginate(query=query, page=page, page_size=page_size)

    async def read_by_id(self, run_id: int) -> Run:
        run = await self._session.get(Run, run_id)
        if run is None:
            raise RunNotFoundException
        return run

    async def create(self, transfer_id: int) -> Run:
        run = Run()
        run.transfer_id = transfer_id
        run.transfer_dump = await self.read_full_serialized_transfer(transfer_id)
        try:
            self._session.add(run)
            await self._session.flush()
            return run
        except IntegrityError as e:
            self._raise_error(e)

    async def update(self, run_id: int, **kwargs: Any) -> Run:
        try:
            return await self._update(Run.id == run_id, **kwargs)
        except IntegrityError as e:
            self._raise_error(e)

    async def stop(self, run_id: int) -> Run:
        run = await self.read_by_id(run_id=run_id)
        if run.status not in [Status.CREATED, Status.STARTED]:
            raise CannotStopRunException(run_id=run_id, current_status=run.status)
        run.status = Status.SEND_STOP_SIGNAL
        await self._session.flush()
        return run

    async def read_full_serialized_transfer(self, transfer_id: int) -> dict[str, Any]:
        transfer = await self._session.get(
            Transfer,
            transfer_id,
            options=(
                joinedload(Transfer.source_connection),
                joinedload(Transfer.target_connection),
            ),
        )
        return ReadFullTransferSchema.from_orm(transfer).dict()

    def _raise_error(self, e: DBAPIError) -> NoReturn:
        constraint = e.__cause__.__cause__.constraint_name  # type: ignore[union-attr]
        if constraint == "fk__run__transfer_id__transfer":
            raise TransferNotFound from e
        raise SyncmasterException from e
