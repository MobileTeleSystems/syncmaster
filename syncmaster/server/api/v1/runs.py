# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import asyncio
from datetime import datetime
from typing import Annotated

from celery import Celery
from fastapi import APIRouter, Depends, Query
from kombu.exceptions import KombuError

from syncmaster.db.models import RunType, Status, User
from syncmaster.db.utils import Permission
from syncmaster.errors.registration import get_error_responses
from syncmaster.exceptions.base import ActionNotAllowedError
from syncmaster.exceptions.run import CannotConnectToTaskQueueError
from syncmaster.exceptions.transfer import TransferNotFoundError
from syncmaster.schemas.v1.connections.connection_base import ReadAuthDataSchema
from syncmaster.schemas.v1.transfers.run import (
    CreateRunSchema,
    ReadRunSchema,
    RunPageSchema,
)
from syncmaster.server.dependencies import Stub
from syncmaster.server.services.get_user import get_user
from syncmaster.server.services.unit_of_work import UnitOfWork

router = APIRouter(tags=["Runs"], responses=get_error_responses())


@router.get("/runs")
async def read_runs(
    transfer_id: int,
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=50, default=20),  # noqa: WPS432
    status: list[Status] | None = Query(default=None),
    started_at_since: datetime | None = Query(default=None),
    started_at_until: datetime | None = Query(default=None),
    current_user: User = Depends(get_user(is_active=True)),
) -> RunPageSchema:
    """Return runs of transfer with pagination"""
    resource_rule = await unit_of_work.transfer.get_resource_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_rule == Permission.NONE:
        raise TransferNotFoundError

    pagination = await unit_of_work.run.paginate(
        transfer_id=transfer_id,
        page=page,
        page_size=page_size,
        status=status,
        started_at_since=started_at_since,
        started_at_until=started_at_until,
    )

    return RunPageSchema.from_pagination(pagination=pagination)


@router.get("/runs/{run_id}")
async def read_run(
    run_id: int,
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
    current_user: User = Depends(get_user(is_active=True)),
) -> ReadRunSchema:
    run = await unit_of_work.run.read_by_id(run_id=run_id)

    resource_role = await unit_of_work.transfer.get_resource_permission(
        user=current_user,
        resource_id=run.transfer_id,
    )

    if resource_role == Permission.NONE:
        raise TransferNotFoundError

    return ReadRunSchema.model_validate(run)


@router.post("/runs")
async def start_run(  # noqa: WPS217
    create_run_data: CreateRunSchema,
    celery: Annotated[Celery, Depends(Stub(Celery))],
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
    current_user: User = Depends(get_user(is_active=True)),
) -> ReadRunSchema:
    # Check: user can start transfer
    resource_rule = await unit_of_work.transfer.get_resource_permission(
        user=current_user,
        resource_id=create_run_data.transfer_id,
    )

    if resource_rule == Permission.NONE:
        raise TransferNotFoundError

    if resource_rule < Permission.WRITE:
        raise ActionNotAllowedError

    transfer = await unit_of_work.transfer.read_by_id(transfer_id=create_run_data.transfer_id)

    # The credentials.read method is used rather than credentials.read_bulk deliberately
    # it’s more convenient to transfer credits in this place
    credentials_source = await unit_of_work.credentials.read(
        transfer.source_connection_id,
    )
    credentials_target = await unit_of_work.credentials.read(
        transfer.target_connection_id,
    )

    async with unit_of_work:
        run = await unit_of_work.run.create(
            transfer_id=create_run_data.transfer_id,
            # Since fields with credentials may have different names (for example, S3 and Postgres have different names)
            # the work of checking fields and removing passwords is delegated to the ReadAuthDataSchema class
            source_creds=ReadAuthDataSchema(auth_data=credentials_source).model_dump(),
            target_creds=ReadAuthDataSchema(auth_data=credentials_target).model_dump(),
            type=RunType.MANUAL,
        )

    try:
        await asyncio.to_thread(
            celery.send_task,
            "run_transfer_task",
            kwargs={"run_id": run.id},
            queue=transfer.queue.slug,
        )
    except KombuError as e:
        async with unit_of_work:
            run = await unit_of_work.run.update(
                run_id=run.id,
                status=Status.FAILED,
            )
        raise CannotConnectToTaskQueueError(run_id=run.id) from e
    return ReadRunSchema.model_validate(run)


@router.post("/runs/{run_id}/stop")
async def stop_run(
    run_id: int,
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
    current_user: User = Depends(get_user(is_active=True)),
) -> ReadRunSchema:
    run = await unit_of_work.run.read_by_id(run_id=run_id)

    # Check: user can stop transfer
    resource_rule = await unit_of_work.transfer.get_resource_permission(
        user=current_user,
        resource_id=run.transfer_id,
    )

    if resource_rule == Permission.NONE:
        raise TransferNotFoundError

    if resource_rule < Permission.WRITE:
        raise ActionNotAllowedError

    async with unit_of_work:
        run = await unit_of_work.run.stop(run_id=run_id)
        # TODO: add immediate stop transfer after stop Run
    return ReadRunSchema.model_validate(run)
