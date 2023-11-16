import asyncio

from fastapi import APIRouter, Depends, Query, status
from kombu.exceptions import KombuError

from app.api.deps import UnitOfWorkMarker
from app.api.v1.schemas import StatusCopyTransferResponseSchema, StatusResponseSchema
from app.api.v1.transfers.schemas import (
    CopyTransferSchema,
    CreateTransferSchema,
    ReadRunSchema,
    ReadTransferSchema,
    RunPageSchema,
    TransferPageSchema,
    UpdateTransferSchema,
)
from app.db.models import Status, User
from app.db.utils import Permission
from app.exceptions import (
    CannotConnectToTaskQueueError,
    ConnectionNotFound,
    DifferentTransferAndConnectionsGroups,
    DifferentTypeConnectionsAndParams,
    GroupNotFound,
    TransferNotFound,
)
from app.exceptions.base import ActionNotAllowed
from app.services import UnitOfWork, get_user
from app.tasks.config import celery

router = APIRouter(tags=["Transfers"])


@router.get("/transfers")
async def read_transfers(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> TransferPageSchema:
    """Return transfers in page format"""
    resource_role = await unit_of_work.group.get_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_role == Permission.NONE:
        raise GroupNotFound

    pagination = await unit_of_work.transfer.paginate(
        page=page,
        page_size=page_size,
        group_id=group_id,
    )

    return TransferPageSchema.from_pagination(pagination=pagination)


@router.post("/transfers")
async def create_transfer(
    transfer_data: CreateTransferSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadTransferSchema:
    group_permission = await unit_of_work.group.get_permission(
        user=current_user,
        group_id=transfer_data.group_id,
    )

    if group_permission < Permission.WRITE:
        raise ActionNotAllowed

    target_connection = await unit_of_work.connection.read_by_id(
        connection_id=transfer_data.target_connection_id,
    )

    source_connection = await unit_of_work.connection.read_by_id(
        connection_id=transfer_data.source_connection_id,
    )

    if (
        target_connection.group_id != source_connection.group_id
        or target_connection.group_id != transfer_data.group_id
        or source_connection.group_id != transfer_data.group_id
    ):
        raise DifferentTransferAndConnectionsGroups

    if target_connection.data["type"] != transfer_data.target_params.type:
        raise DifferentTypeConnectionsAndParams(
            connection_type=target_connection.data["type"],
            conn="target",
            params_type=transfer_data.target_params.type,
        )

    if source_connection.data["type"] != transfer_data.source_params.type:
        raise DifferentTypeConnectionsAndParams(
            connection_type=source_connection.data["type"],
            conn="source",
            params_type=transfer_data.source_params.type,
        )

    async with unit_of_work:
        transfer = await unit_of_work.transfer.create(
            group_id=transfer_data.group_id,
            name=transfer_data.name,
            description=transfer_data.description,
            target_connection_id=transfer_data.target_connection_id,
            source_connection_id=transfer_data.source_connection_id,
            source_params=transfer_data.source_params.dict(),
            target_params=transfer_data.target_params.dict(),
            strategy_params=transfer_data.strategy_params.dict(),
        )
    return ReadTransferSchema.from_orm(transfer)


@router.get("/transfers/{transfer_id}")
async def read_transfer(
    transfer_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadTransferSchema:
    """Return transfer data by transfer ID"""
    resource_role = await unit_of_work.transfer.get_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_role == Permission.NONE:
        raise TransferNotFound

    transfer = await unit_of_work.transfer.read_by_id(transfer_id=transfer_id)
    return ReadTransferSchema.from_orm(transfer)


@router.post("/transfers/{transfer_id}/copy_transfer")
async def copy_transfer(
    transfer_id: int,
    transfer_data: CopyTransferSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusCopyTransferResponseSchema:
    # Check: user can copy transfer
    target_source_transfer_rules = await asyncio.gather(
        unit_of_work.transfer.get_permission(
            user=current_user,
            resource_id=transfer_id,
        ),
        unit_of_work.group.get_permission(
            user=current_user,
            group_id=transfer_data.new_group_id,
        ),
    )
    resource_role, target_group_role = target_source_transfer_rules

    if resource_role == Permission.NONE:
        raise TransferNotFound

    if target_group_role < Permission.WRITE:
        raise ActionNotAllowed

    # Check: user can delete transfer
    if transfer_data.remove_source and resource_role < Permission.DELETE:
        raise ActionNotAllowed

    transfer = await unit_of_work.transfer.read_by_id(transfer_id=transfer_id)
    # Check: user can copy connection
    target_source_connection_rules = await asyncio.gather(
        unit_of_work.connection.get_permission(
            user=current_user,
            resource_id=transfer.source_connection_id,
        ),
        unit_of_work.connection.get_permission(
            user=current_user,
            resource_id=transfer.target_connection_id,
        ),
    )
    source_connection_role, target_connection_role = target_source_connection_rules

    if source_connection_role == Permission.NONE or target_connection_role == Permission.NONE:
        raise ConnectionNotFound

    async with unit_of_work:
        copied_source_connection = await unit_of_work.connection.copy(
            connection_id=transfer.source_connection_id,
            new_group_id=transfer_data.new_group_id,
        )

        copied_target_connection = copied_source_connection

        if transfer.source_connection_id != transfer.target_connection_id:  # Source and target are not the same
            copied_target_connection = await unit_of_work.connection.copy(
                connection_id=transfer.target_connection_id,
                new_group_id=transfer_data.new_group_id,
            )

        copied_transfer = await unit_of_work.transfer.copy(
            transfer_id=transfer_id,
            new_group_id=transfer_data.new_group_id,
            new_source_connection=copied_source_connection.id,
            new_target_connection=copied_target_connection.id,
        )

        if transfer_data.remove_source:
            await unit_of_work.transfer.delete(transfer_id=transfer_id)

    return StatusCopyTransferResponseSchema(
        ok=True,
        status_code=status.HTTP_200_OK,
        message="Transfer was copied.",
        source_connection_id=copied_source_connection.id,
        target_connection_id=copied_target_connection.id,
        copied_transfer_id=copied_transfer.id,
    )


@router.patch("/transfers/{transfer_id}")
async def update_transfer(
    transfer_id: int,
    transfer_data: UpdateTransferSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadTransferSchema:
    # Check: user can update transfer
    resource_role = await unit_of_work.transfer.get_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_role == Permission.NONE:
        raise TransferNotFound

    if resource_role < Permission.WRITE:
        raise ActionNotAllowed

    transfer = await unit_of_work.transfer.read_by_id(
        transfer_id=transfer_id,
    )

    target_connection = await unit_of_work.connection.read_by_id(
        connection_id=transfer_data.target_connection_id or transfer.target_connection_id,
    )
    source_connection = await unit_of_work.connection.read_by_id(
        connection_id=transfer_data.source_connection_id or transfer.source_connection_id,
    )

    # Check: user can read new connections
    target_resource_role = await unit_of_work.connection.get_permission(
        user=current_user,
        resource_id=target_connection.id,
    )

    source_resource_role = await unit_of_work.connection.get_permission(
        user=current_user,
        resource_id=source_connection.id,
    )

    if source_resource_role == Permission.NONE or target_resource_role == Permission.NONE:
        raise ConnectionNotFound

    # Check: connections and transfer group
    if (
        target_connection.group_id != source_connection.group_id
        or target_connection.group_id != transfer.group_id
        or source_connection.group_id != transfer.group_id
    ):
        raise DifferentTransferAndConnectionsGroups

    if transfer_data.target_params and target_connection.data["type"] != transfer_data.target_params.type:
        raise DifferentTypeConnectionsAndParams(
            connection_type=target_connection.data["type"],
            conn="target",
            params_type=transfer_data.target_params.type,
        )

    if transfer_data.source_params and source_connection.data["type"] != transfer_data.source_params.type:
        raise DifferentTypeConnectionsAndParams(
            connection_type=source_connection.data["type"],
            conn="source",
            params_type=transfer_data.source_params.type,
        )

    async with unit_of_work:
        transfer = await unit_of_work.transfer.update(
            transfer=transfer,
            name=transfer_data.name,
            description=transfer_data.description,
            target_connection_id=transfer_data.target_connection_id,
            source_connection_id=transfer_data.source_connection_id,
            source_params=transfer_data.source_params.dict() if transfer_data.source_params else {},
            target_params=transfer_data.target_params.dict() if transfer_data.target_params else {},
            strategy_params=transfer_data.strategy_params.dict() if transfer_data.strategy_params else {},
            is_scheduled=transfer_data.is_scheduled,
            schedule=transfer_data.schedule,
        )
    return ReadTransferSchema.from_orm(transfer)


@router.delete("/transfers/{transfer_id}")
async def delete_transfer(
    transfer_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    resource_role = await unit_of_work.transfer.get_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_role == Permission.NONE:
        raise TransferNotFound

    if resource_role < Permission.DELETE:
        raise ActionNotAllowed

    async with unit_of_work:
        await unit_of_work.transfer.delete(
            transfer_id=transfer_id,
        )

    return StatusResponseSchema(
        ok=True,
        status_code=status.HTTP_200_OK,
        message="Transfer was deleted",
    )


@router.get("/transfers/{transfer_id}/runs")
async def read_runs(
    transfer_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> RunPageSchema:
    """Return runs of transfer with pagination"""
    resource_rule = await unit_of_work.transfer.get_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_rule == Permission.NONE:
        raise GroupNotFound

    pagination = await unit_of_work.run.paginate(
        transfer_id=transfer_id,
        page=page,
        page_size=page_size,
    )

    return RunPageSchema.from_pagination(pagination=pagination)


@router.get("/transfers/{transfer_id}/runs/{run_id}")
async def read_run(
    transfer_id: int,
    run_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadRunSchema:
    resource_role = await unit_of_work.transfer.get_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_role == Permission.NONE:
        raise TransferNotFound

    run = await unit_of_work.run.read_by_id(run_id=run_id)
    return ReadRunSchema.from_orm(run)


@router.post("/transfers/{transfer_id}/runs")
async def start_run(
    transfer_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadRunSchema:
    # Check: user can start transfer
    resource_rule = await unit_of_work.transfer.get_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_rule == Permission.NONE:
        raise TransferNotFound

    if resource_rule < Permission.WRITE:
        raise ActionNotAllowed

    async with unit_of_work:
        run = await unit_of_work.run.create(transfer_id=transfer_id)
    try:
        celery.send_task("run_transfer_task", kwargs={"run_id": run.id})
    except KombuError as e:
        async with unit_of_work:
            run = await unit_of_work.run.update(
                run_id=run.id,
                status=Status.FAILED,
            )
        raise CannotConnectToTaskQueueError(run_id=run.id) from e
    return ReadRunSchema.from_orm(run)


@router.post("/transfers/{transfer_id}/runs/{run_id}/stop")
async def stop_run(
    transfer_id: int,
    run_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadRunSchema:
    # Check: user can stop transfer
    resource_rule = await unit_of_work.transfer.get_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_rule == Permission.NONE:
        raise TransferNotFound

    if resource_rule < Permission.WRITE:
        raise ActionNotAllowed

    async with unit_of_work:
        run = await unit_of_work.run.stop(run_id=run_id)
        # TODO add immdiate stop transfer after stop Run
    return ReadRunSchema.from_orm(run)
