# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from http.client import NO_CONTENT
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from syncmaster.db.models import User
from syncmaster.db.utils import Permission
from syncmaster.errors.registration import get_error_responses
from syncmaster.exceptions import ActionNotAllowedError
from syncmaster.exceptions.group import GroupNotFoundError
from syncmaster.exceptions.queue import QueueDeleteError, QueueNotFoundError
from syncmaster.schemas.v1.queue import (
    CreateQueueSchema,
    QueuePageSchema,
    ReadQueueSchema,
    UpdateQueueSchema,
)
from syncmaster.server.services.get_user import get_user
from syncmaster.server.services.unit_of_work import UnitOfWork

router = APIRouter(tags=["Queues"], responses=get_error_responses())


@router.get("/queues", description="Queues in page format")
async def read_queues(  # noqa: PLR0913
    group_id: int,
    current_user: Annotated[User, Depends(get_user())],
    unit_of_work: Annotated[UnitOfWork, Depends(UnitOfWork)],
    page: Annotated[int, Query(gt=0)] = 1,
    page_size: Annotated[int, Query(gt=0, le=50)] = 20,
    search_query: Annotated[
        str | None,
        Query(
            title="Search Query",
            description="full-text search for queues",
        ),
    ] = None,
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
        search_query=search_query,
    )
    return QueuePageSchema.from_pagination(pagination=pagination)


@router.get("/queues/{queue_id}", description="Read queue by id")
async def read_queue(
    queue_id: int,
    current_user: Annotated[User, Depends(get_user())],
    unit_of_work: Annotated[UnitOfWork, Depends(UnitOfWork)],
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
    return ReadQueueSchema.model_validate(queue, from_attributes=True)


@router.post("/queues", description="Create new queue")
async def create_queue(
    queue_data: CreateQueueSchema,
    current_user: Annotated[User, Depends(get_user())],
    unit_of_work: Annotated[UnitOfWork, Depends(UnitOfWork)],
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
        queue = await unit_of_work.queue.create(queue_data.model_dump(mode="json"))

    return ReadQueueSchema.model_validate(queue, from_attributes=True)


@router.put("/queues/{queue_id}", description="Updating queue information")
async def update_queue(
    queue_id: int,
    queue_data: UpdateQueueSchema,
    current_user: Annotated[User, Depends(get_user())],
    unit_of_work: Annotated[UnitOfWork, Depends(UnitOfWork)],
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
            name=queue_data.name,
            description=queue_data.description,
        )
    return ReadQueueSchema.model_validate(queue, from_attributes=True)


@router.delete("/queues/{queue_id}", description="Delete queue by id", status_code=NO_CONTENT)
async def delete_queue(
    queue_id: int,
    current_user: Annotated[User, Depends(get_user())],
    unit_of_work: Annotated[UnitOfWork, Depends(UnitOfWork)],
):
    resource_role = await unit_of_work.queue.get_resource_permission(
        user=current_user,
        resource_id=queue_id,
    )

    if resource_role == Permission.NONE:
        raise QueueNotFoundError

    if resource_role < Permission.DELETE:
        raise ActionNotAllowedError

    queue = await unit_of_work.queue.read_by_id(queue_id=queue_id)
    transfers = await unit_of_work.transfer.paginate(group_id=queue.group_id, queue_id=queue.id, page=1, page_size=1)
    if transfers.items:
        msg = f"The queue has an associated transfers(s). Number of the linked transfers: {transfers.total}"
        raise QueueDeleteError(msg)

    async with unit_of_work:
        await unit_of_work.queue.delete(queue_id=queue_id)
