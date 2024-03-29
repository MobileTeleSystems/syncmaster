# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from fastapi import APIRouter, Depends, Query, status

from syncmaster.backend.api.deps import UnitOfWorkMarker
from syncmaster.backend.services import UnitOfWork, get_user
from syncmaster.db.models import User
from syncmaster.db.utils import Permission
from syncmaster.exceptions import ActionNotAllowedError
from syncmaster.exceptions.group import GroupNotFoundError
from syncmaster.exceptions.queue import QueueDeleteError, QueueNotFoundError
from syncmaster.schemas.v1.queue import (
    CreateQueueSchema,
    QueuePageSchema,
    ReadQueueSchema,
    UpdateQueueSchema,
)
from syncmaster.schemas.v1.status import StatusResponseSchema

router = APIRouter(tags=["Queues"])


@router.get("/queues/{queue_id}", description="Read queue by id")
async def read_queue(
    queue_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadQueueSchema:
    resource_role = await unit_of_work.queue.get_resource_permission(
        user=current_user,
        resource_id=queue_id,
    )

    if resource_role == Permission.NONE:
        raise QueueNotFoundError

    queue = await unit_of_work.queue.read_by_id(
        queue_id=queue_id,
    )
    return ReadQueueSchema.from_orm(queue)


@router.post("/queues", description="Create new queue")
async def create_queue(
    queue_data: CreateQueueSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadQueueSchema:
    group_permission = await unit_of_work.queue.get_group_permission(
        user=current_user,
        group_id=queue_data.group_id,
    )
    if group_permission == Permission.NONE:
        raise GroupNotFoundError

    if group_permission < Permission.DELETE:
        raise ActionNotAllowedError

    async with unit_of_work:
        queue = await unit_of_work.queue.create(queue_data.dict())

    return ReadQueueSchema.from_orm(queue)


@router.patch("/queues/{queue_id}", description="Updating queue information")
async def update_queue(
    queue_id: int,
    queue_data: UpdateQueueSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadQueueSchema:
    resource_role = await unit_of_work.queue.get_resource_permission(
        user=current_user,
        resource_id=queue_id,
    )

    if resource_role == Permission.NONE:
        raise QueueNotFoundError

    if resource_role < Permission.DELETE:
        raise ActionNotAllowedError

    async with unit_of_work:
        queue = await unit_of_work.queue.update(
            queue_id=queue_id,
            queue_data=queue_data,
        )
    return ReadQueueSchema.from_orm(queue)


@router.delete("/queues/{queue_id}", description="Delete queue by id")
async def delete_queue(
    queue_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    resource_role = await unit_of_work.queue.get_resource_permission(
        user=current_user,
        resource_id=queue_id,
    )

    if resource_role == Permission.NONE:
        raise QueueNotFoundError

    if resource_role < Permission.DELETE:
        raise ActionNotAllowedError

    queue = await unit_of_work.queue.read_by_id(queue_id=queue_id)

    transfers = queue.transfers

    if transfers:
        raise QueueDeleteError(
            f"The queue has an associated transfers(s). Number of the linked transfers: {len(transfers)}",
        )

    async with unit_of_work:
        await unit_of_work.queue.delete(queue_id=queue_id)

    return StatusResponseSchema(
        ok=True,
        status_code=status.HTTP_200_OK,
        message="Queue was deleted",
    )


@router.get("/queues", description="Queues in page format")
async def read_queues(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> QueuePageSchema:
    resource_role = await unit_of_work.queue.get_group_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_role == Permission.NONE:
        raise GroupNotFoundError

    pagination = await unit_of_work.queue.paginate(
        page=page,
        page_size=page_size,
        group_id=group_id,
    )
    return QueuePageSchema.from_pagination(pagination=pagination)
