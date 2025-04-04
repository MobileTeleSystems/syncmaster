# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from http.client import NO_CONTENT

from fastapi import APIRouter, Depends, Query

from syncmaster.db.models import ConnectionType, User
from syncmaster.db.utils import Permission
from syncmaster.errors.registration import get_error_responses
from syncmaster.exceptions.base import ActionNotAllowedError
from syncmaster.exceptions.connection import ConnectionNotFoundError
from syncmaster.exceptions.group import GroupNotFoundError
from syncmaster.exceptions.queue import DifferentTransferAndQueueGroupError
from syncmaster.exceptions.transfer import (
    DifferentTransferAndConnectionsGroupsError,
    DifferentTypeConnectionsAndParamsError,
    TransferNotFoundError,
)
from syncmaster.schemas.v1.transfers import (
    CopyTransferSchema,
    CreateTransferSchema,
    ReadTransferSchema,
    TransferPageSchema,
)
from syncmaster.server.services.get_user import get_user
from syncmaster.server.services.unit_of_work import UnitOfWork

router = APIRouter(tags=["Transfers"], responses=get_error_responses())


@router.get("/transfers")
async def read_transfers(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=50, default=20),  # noqa: WPS432
    search_query: str | None = Query(
        None,
        title="Search Query",
        description="full-text search for transfer",
    ),
    source_connection_id: int | None = Query(None),
    target_connection_id: int | None = Query(None),
    queue_id: int | None = Query(None),
    source_connection_type: list[ConnectionType] | None = Query(None),
    target_connection_type: list[ConnectionType] | None = Query(None),
    is_scheduled: bool | None = Query(None),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> TransferPageSchema:
    """Return transfers in page format"""
    resource_role = await unit_of_work.transfer.get_group_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_role == Permission.NONE:
        raise GroupNotFoundError

    source_connection_str_type = None if source_connection_type is None else [ct.value for ct in source_connection_type]
    target_connection_str_type = None if target_connection_type is None else [ct.value for ct in target_connection_type]

    pagination = await unit_of_work.transfer.paginate(
        page=page,
        page_size=page_size,
        group_id=group_id,
        search_query=search_query,
        source_connection_id=source_connection_id,
        target_connection_id=target_connection_id,
        queue_id=queue_id,
        source_connection_type=source_connection_str_type,
        target_connection_type=target_connection_str_type,
        is_scheduled=is_scheduled,
    )

    return TransferPageSchema.from_pagination(pagination=pagination)


@router.post("/transfers")
async def create_transfer(  # noqa: WPS217, WPS238
    transfer_data: CreateTransferSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> ReadTransferSchema:
    group_permission = await unit_of_work.transfer.get_group_permission(
        user=current_user,
        group_id=transfer_data.group_id,
    )
    if group_permission < Permission.WRITE:
        raise ActionNotAllowedError

    target_connection = await unit_of_work.connection.read_by_id(transfer_data.target_connection_id)
    source_connection = await unit_of_work.connection.read_by_id(transfer_data.source_connection_id)
    queue = await unit_of_work.queue.read_by_id(transfer_data.queue_id)

    if (
        target_connection.group_id != source_connection.group_id
        or target_connection.group_id != transfer_data.group_id
        or source_connection.group_id != transfer_data.group_id
    ):
        raise DifferentTransferAndConnectionsGroupsError

    if target_connection.type != transfer_data.target_params.type:
        raise DifferentTypeConnectionsAndParamsError(
            connection_type=target_connection.type,
            conn="target",
            params_type=transfer_data.target_params.type,
        )

    if source_connection.type != transfer_data.source_params.type:
        raise DifferentTypeConnectionsAndParamsError(
            connection_type=source_connection.type,
            conn="source",
            params_type=transfer_data.source_params.type,
        )

    if transfer_data.group_id != queue.group_id:
        raise DifferentTransferAndQueueGroupError

    async with unit_of_work:
        transfer = await unit_of_work.transfer.create(
            group_id=transfer_data.group_id,
            name=transfer_data.name,
            description=transfer_data.description,
            target_connection_id=transfer_data.target_connection_id,
            source_connection_id=transfer_data.source_connection_id,
            source_params=transfer_data.source_params.model_dump(),
            target_params=transfer_data.target_params.model_dump(),
            strategy_params=transfer_data.strategy_params.model_dump(),
            transformations=[tr.model_dump() for tr in transfer_data.transformations],
            resources=transfer_data.resources.model_dump(),
            queue_id=transfer_data.queue_id,
            is_scheduled=transfer_data.is_scheduled,
            schedule=transfer_data.schedule,
        )
    return ReadTransferSchema.model_validate(transfer, from_attributes=True)


@router.get("/transfers/{transfer_id}")
async def read_transfer(
    transfer_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> ReadTransferSchema:
    """Return transfer data by transfer ID"""
    resource_role = await unit_of_work.transfer.get_resource_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_role == Permission.NONE:
        raise TransferNotFoundError

    transfer = await unit_of_work.transfer.read_by_id(transfer_id=transfer_id)
    return ReadTransferSchema.model_validate(transfer, from_attributes=True)


@router.post("/transfers/{transfer_id}/copy_transfer")
async def copy_transfer(  # noqa: WPS217, WPS238
    transfer_id: int,
    transfer_data: CopyTransferSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> ReadTransferSchema:
    resource_role = await unit_of_work.transfer.get_resource_permission(
        user=current_user,
        resource_id=transfer_id,
    )
    if resource_role == Permission.NONE:
        raise TransferNotFoundError

    # Check: user can delete transfer
    if transfer_data.remove_source and resource_role < Permission.DELETE:
        raise ActionNotAllowedError

    target_group_role = await unit_of_work.transfer.get_group_permission(
        user=current_user,
        group_id=transfer_data.new_group_id,
    )
    if target_group_role < Permission.WRITE:
        raise ActionNotAllowedError

    transfer = await unit_of_work.transfer.read_by_id(transfer_id=transfer_id)

    # Check: user can copy connection
    source_connection_role = await unit_of_work.connection.get_resource_permission(
        user=current_user,
        resource_id=transfer.source_connection_id,
    )
    if source_connection_role == Permission.NONE:
        raise ConnectionNotFoundError

    target_connection_role = await unit_of_work.connection.get_resource_permission(
        user=current_user,
        resource_id=transfer.target_connection_id,
    )
    if target_connection_role == Permission.NONE:
        raise ConnectionNotFoundError

    # Check: new queue exists
    new_queue = await unit_of_work.queue.read_by_id(queue_id=transfer_data.new_queue_id)

    # Acheck: new_queue_id and new_group_id are similar
    if new_queue.group_id != transfer_data.new_group_id:
        raise DifferentTransferAndQueueGroupError

    async with unit_of_work:
        copied_source_connection = await unit_of_work.connection.copy(
            connection_id=transfer.source_connection_id,
            new_group_id=transfer_data.new_group_id,
            new_name=transfer_data.new_source_connection_name,
        )

        copied_target_connection = copied_source_connection

        if transfer.source_connection_id != transfer.target_connection_id:  # Source and target are not the same
            copied_target_connection = await unit_of_work.connection.copy(
                connection_id=transfer.target_connection_id,
                new_group_id=transfer_data.new_group_id,
                new_name=transfer_data.new_target_connection_name,
            )

        copied_transfer = await unit_of_work.transfer.copy(
            transfer_id=transfer_id,
            new_group_id=transfer_data.new_group_id,
            new_source_connection=copied_source_connection.id,
            new_target_connection=copied_target_connection.id,
            new_queue_id=transfer_data.new_queue_id,
            new_name=transfer_data.new_name,
        )

        if transfer_data.remove_source:
            await unit_of_work.transfer.delete(transfer_id=transfer_id)

    return ReadTransferSchema.model_validate(copied_transfer, from_attributes=True)


@router.put("/transfers/{transfer_id}")
async def update_transfer(  # noqa: WPS217, WPS238
    transfer_id: int,
    transfer_data: CreateTransferSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> ReadTransferSchema:
    # Check: user can update transfer
    resource_role = await unit_of_work.transfer.get_resource_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_role == Permission.NONE:
        raise TransferNotFoundError

    if resource_role < Permission.WRITE:
        raise ActionNotAllowedError

    target_connection = await unit_of_work.connection.read_by_id(transfer_data.target_connection_id)
    source_connection = await unit_of_work.connection.read_by_id(transfer_data.source_connection_id)
    queue = await unit_of_work.queue.read_by_id(transfer_data.queue_id)

    # Check: user can read new connections
    target_connection_resource_role = await unit_of_work.connection.get_resource_permission(
        user=current_user,
        resource_id=target_connection.id,
    )

    source_connection_resource_role = await unit_of_work.connection.get_resource_permission(
        user=current_user,
        resource_id=source_connection.id,
    )

    if source_connection_resource_role == Permission.NONE or target_connection_resource_role == Permission.NONE:
        raise ConnectionNotFoundError

    if (
        target_connection.group_id != source_connection.group_id
        or target_connection.group_id != transfer_data.group_id
        or source_connection.group_id != transfer_data.group_id
    ):
        raise DifferentTransferAndConnectionsGroupsError

    if target_connection.type != transfer_data.target_params.type:
        raise DifferentTypeConnectionsAndParamsError(
            connection_type=target_connection.type,
            conn="target",
            params_type=transfer_data.target_params.type,
        )

    if source_connection.type != transfer_data.source_params.type:
        raise DifferentTypeConnectionsAndParamsError(
            connection_type=source_connection.type,
            conn="source",
            params_type=transfer_data.source_params.type,
        )

    if transfer_data.group_id != queue.group_id:
        raise DifferentTransferAndQueueGroupError

    async with unit_of_work:
        transfer = await unit_of_work.transfer.update(
            transfer_id=transfer_id,
            name=transfer_data.name,
            description=transfer_data.description,
            target_connection_id=transfer_data.target_connection_id,
            source_connection_id=transfer_data.source_connection_id,
            source_params=transfer_data.source_params.model_dump(),
            target_params=transfer_data.target_params.model_dump(),
            strategy_params=transfer_data.strategy_params.model_dump(),
            transformations=[tr.model_dump() for tr in transfer_data.transformations],
            resources=transfer_data.resources.model_dump(),
            is_scheduled=transfer_data.is_scheduled,
            schedule=transfer_data.schedule,
            queue_id=transfer_data.queue_id,
        )
    return ReadTransferSchema.model_validate(transfer, from_attributes=True)


@router.delete("/transfers/{transfer_id}", status_code=NO_CONTENT)
async def delete_transfer(
    transfer_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
):
    resource_role = await unit_of_work.transfer.get_resource_permission(
        user=current_user,
        resource_id=transfer_id,
    )

    if resource_role == Permission.NONE:
        raise TransferNotFoundError

    if resource_role < Permission.DELETE:
        raise ActionNotAllowedError

    async with unit_of_work:
        await unit_of_work.transfer.delete(
            transfer_id=transfer_id,
        )
