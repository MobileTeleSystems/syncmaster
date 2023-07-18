import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_session, get_current_active_user, get_superuser
from app.api.v1.schemas import StatusResponseSchema
from app.api.v1.users.schemas import ReadUserSchema, UpdateUserSchema, UserPageSchema
from app.db.models import User
from app.db.utils import paginate

logger = logging.getLogger(__name__)


router = APIRouter(tags=["Users"])


@router.get("/users")
async def get_users(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> UserPageSchema:
    query = select(User)
    if not current_user.is_superuser:
        query = query.filter_by(is_active=True, is_deleted=False)
    pagination = await paginate(
        query=query, page=page, page_size=page_size, session=session
    )
    return UserPageSchema.from_pagination(pagination)


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> ReadUserSchema:
    user = (
        (
            await session.execute(
                select(User).filter_by(
                    is_deleted=False,
                    is_active=True,
                    id=user_id,
                )
            )
        )
        .scalars()
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return ReadUserSchema.from_orm(user)


@router.post("/users/{user_id}")
async def update_user(
    user_id: int,
    user_data: UpdateUserSchema,
    current_user: User = Depends(get_current_active_user),
    session: AsyncSession = Depends(get_async_session),
) -> ReadUserSchema:
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You cannot change other user"
        )
    change_user = (
        (
            await session.execute(
                select(User).filter_by(
                    is_deleted=False,
                    id=user_id,
                )
            )
        )
        .scalars()
        .first()
    )
    if change_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    try:
        change_user.username = user_data.username
        await session.commit()
    except IntegrityError:
        raise HTTPException(status_code=400, detail="Username is already taken")
    await session.refresh(change_user)
    return ReadUserSchema.from_orm(change_user)


@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_superuser),
    session: AsyncSession = Depends(get_async_session),
) -> StatusResponseSchema:
    user = (
        (await session.execute(select(User).filter_by(is_deleted=False, id=user_id)))
        .scalars()
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    user.is_active = True
    session.add(user)
    await session.commit()
    await session.refresh(user)
    logger.warning("User %s active=%s id=%d", user, user.is_active, user.id)
    return StatusResponseSchema(ok=True, status_code=200, message="User was activated")


@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_superuser),
    session: AsyncSession = Depends(get_async_session),
):
    user = (
        (await session.execute(select(User).filter_by(is_deleted=False, id=user_id)))
        .scalars()
        .first()
    )
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot deactivate superuser user",
        )
    user.is_active = False
    await session.commit()
    return StatusResponseSchema(
        ok=True, status_code=200, message="User was deactivated"
    )
