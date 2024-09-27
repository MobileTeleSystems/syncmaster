# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging

from fastapi import APIRouter, Depends, Query

from syncmaster.backend.api.deps import UnitOfWorkMarker
from syncmaster.backend.services import UnitOfWork, get_user
from syncmaster.db.models import User
from syncmaster.schemas.v1.users import ReadUserSchema, UserPageSchema

logger = logging.getLogger(__name__)


router = APIRouter(tags=["Users"])


@router.get("/users")
async def get_users(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> UserPageSchema:
    pagination = await unit_of_work.user.paginate(
        page=page,
        page_size=page_size,
        is_superuser=current_user.is_superuser,
    )
    return UserPageSchema.from_pagination(pagination)


@router.get("/users/me")
async def read_current_user(
    current_user: User = Depends(get_user(is_active=True)),
) -> ReadUserSchema:
    return ReadUserSchema.from_orm(current_user)


@router.get("/users/{user_id}", dependencies=[Depends(get_user(is_active=True))])
async def read_user(
    user_id: int,
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadUserSchema:
    user = await unit_of_work.user.read_by_id(user_id=user_id, is_active=True)
    return ReadUserSchema.from_orm(user)
