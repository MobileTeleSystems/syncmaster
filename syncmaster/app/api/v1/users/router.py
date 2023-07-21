import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DatabaseProviderMarker
from app.api.services import get_user
from app.api.v1.schemas import StatusResponseSchema
from app.api.v1.users.schemas import ReadUserSchema, UpdateUserSchema, UserPageSchema
from app.db.models import User
from app.db.provider import DatabaseProvider
from app.exceptions import EntityNotFound, UsernameAlreadyExists

logger = logging.getLogger(__name__)


router = APIRouter(tags=["Users"])


@router.get("/users")
async def get_users(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> UserPageSchema:
    pagination = await holder.user.paginate(
        page=page, page_size=page_size, is_superuser=current_user.is_superuser
    )
    return UserPageSchema.from_pagination(pagination)


@router.get("/users/{user_id}", dependencies=[Depends(get_user(is_active=True))])
async def read_user(
    user_id: int, holder: DatabaseProvider = Depends(DatabaseProviderMarker)
) -> ReadUserSchema:
    try:
        user = await holder.user.read_by_id(user_id=user_id, is_active=True)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        ) from e
    return ReadUserSchema.from_orm(user)


@router.post("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UpdateUserSchema,
    current_user: User = Depends(get_user(is_active=True)),
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadUserSchema:
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot change other user"
        )
    try:
        change_user = await holder.user.update(user_id=user_id, data=user_data.dict())
    except UsernameAlreadyExists as e:
        raise HTTPException(
            status_code=400,
            detail="Username is already taken",
        ) from e
    except EntityNotFound as e:
        raise HTTPException(status_code=404, detail="User not found") from e
    return ReadUserSchema.from_orm(change_user)


@router.post(
    "/users/{user_id}/activate", dependencies=[Depends(get_user(is_superuser=True))]
)
async def activate_user(
    user_id: int,
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    try:
        user = await holder.user.update(user_id=user_id, data={"is_active": True})
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from e
    logger.info("User %s active=%s id=%d", user, user.is_active, user.id)
    return StatusResponseSchema(ok=True, status_code=200, message="User was activated")


@router.post(
    "/users/{user_id}/deactivate", dependencies=[Depends(get_user(is_superuser=True))]
)
async def deactivate_user(
    user_id: int,
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
):
    try:
        user = await holder.user.update(user_id=user_id, data={"is_active": False})
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        ) from e
    logger.info("User %s active=%s id=%d", user, user.is_active, user.id)
    return StatusResponseSchema(
        ok=True, status_code=200, message="User was deactivated"
    )
