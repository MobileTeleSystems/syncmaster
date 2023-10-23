from fastapi import APIRouter, Depends, Query, status

from app.api.deps import DatabaseProviderMarker
from app.api.services import get_user
from app.api.v1.queue.schemas import (
    CreateQueueSchema,
    QueuePageSchema,
    ReadQueueSchema,
    UpdateQueueSchema,
)
from app.api.v1.schemas import StatusResponseSchema
from app.db.models import User
from app.db.provider import DatabaseProvider
from app.exceptions import ActionNotAllowed, QueueDeleteException

router = APIRouter(tags=["Queues"])


@router.post("/queues", description="Create new queue")
async def create_queue(
    queue_data: CreateQueueSchema,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadQueueSchema:
    if not current_user.is_superuser:
        raise ActionNotAllowed

    queue = await provider.queue.create(
        name=queue_data.name,
        description=queue_data.description,
        is_active=queue_data.is_active,
    )

    return ReadQueueSchema.from_orm(queue)


@router.get("/queues/{queue_id}", description="Read queue by id")
async def read_queue(
    queue_id: int,
    _user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadQueueSchema:
    queue = await provider.queue.read_by_id(
        queue_id=queue_id,
    )
    return ReadQueueSchema.from_orm(queue)


@router.get("/queues", description="Queues in page format")
async def read_queues(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    _user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> QueuePageSchema:
    pagination = await provider.queue.paginate(
        page=page,
        page_size=page_size,
    )
    return QueuePageSchema.from_pagination(pagination=pagination)


@router.patch("/queues/{queue_id}", description="Updating queue information")
async def update_queue(
    queue_id: int,
    queue_data: UpdateQueueSchema,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadQueueSchema:
    if not current_user.is_superuser:
        raise ActionNotAllowed

    queue = await provider.queue.update(
        queue_id=queue_id,
        name=queue_data.name,
        description=queue_data.description,
        is_active=queue_data.is_active,
    )
    return ReadQueueSchema.from_orm(queue)


@router.delete("/queues/{queue_id}", description="Delete queue by id")
async def delete_queue(
    queue_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    if not current_user.is_superuser:
        raise ActionNotAllowed

    queue = await provider.queue.read_by_id(
        queue_id=queue_id,
    )

    connections = queue.connections

    if not connections:
        await provider.queue.delete(queue_id=queue_id)
        return StatusResponseSchema(
            ok=True,
            status_code=status.HTTP_200_OK,
            message="Queue was deleted",
        )

    raise QueueDeleteException(
        f"The queue has an associated connection(s). Number of the connected connections: {len(connections)}",
    )
