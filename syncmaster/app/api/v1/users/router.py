import logging

from fastapi import APIRouter, Depends, Query

from app.api.deps import DatabaseProviderMarker
from app.api.services import get_user
from app.api.v1.schemas import StatusResponseSchema
from app.api.v1.users.schemas import ReadUserSchema, UpdateUserSchema, UserPageSchema
from app.db.models import User
from app.db.provider import DatabaseProvider
from app.exceptions import ActionNotAllowed

logger = logging.getLogger(__name__)


router = APIRouter(tags=["Users"])


@router.get("/users")
async def get_users(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> UserPageSchema:
    pagination = await provider.user.paginate(
        page=page, page_size=page_size, is_superuser=current_user.is_superuser
    )
    return UserPageSchema.from_pagination(pagination)


@router.get("/users/{user_id}", dependencies=[Depends(get_user(is_active=True))])
async def read_user(
    user_id: int, provider: DatabaseProvider = Depends(DatabaseProviderMarker)
) -> ReadUserSchema:
    user = await provider.user.read_by_id(user_id=user_id, is_active=True)
    return ReadUserSchema.from_orm(user)


@router.patch("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UpdateUserSchema,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadUserSchema:
    if user_id != current_user.id and not current_user.is_superuser:
        raise ActionNotAllowed
    change_user = await provider.user.update(user_id=user_id, data=user_data.dict())
    return ReadUserSchema.from_orm(change_user)


@router.post(
    "/users/{user_id}/activate", dependencies=[Depends(get_user(is_superuser=True))]
)
async def activate_user(
    user_id: int,
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    user = await provider.user.update(user_id=user_id, data={"is_active": True})
    logger.info("User %s active=%s id=%d", user, user.is_active, user.id)
    return StatusResponseSchema(ok=True, status_code=200, message="User was activated")


@router.post(
    "/users/{user_id}/deactivate", dependencies=[Depends(get_user(is_superuser=True))]
)
async def deactivate_user(
    user_id: int,
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
):
    user = await provider.user.update(user_id=user_id, data={"is_active": False})
    logger.info("User %s active=%s id=%d", user, user.is_active, user.id)
    return StatusResponseSchema(
        ok=True, status_code=200, message="User was deactivated"
    )
