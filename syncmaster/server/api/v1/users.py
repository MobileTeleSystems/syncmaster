# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging

from fastapi import APIRouter, Depends, Query

from syncmaster.db.models import User
from syncmaster.errors.registration import get_error_responses
from syncmaster.schemas.v1.users import ReadUserSchema, UserPageSchema
from syncmaster.server.services.get_user import get_user
from syncmaster.server.services.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


router = APIRouter(tags=["Users"], responses=get_error_responses())


@router.get("/users")
async def get_users(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=50, default=20),  # noqa: WPS432
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
    search_query: str | None = Query(
        None,
        title="Search Query",
        description="fuzzy search for users",
    ),
) -> UserPageSchema:
    pagination = await unit_of_work.user.paginate(
        page=page,
        page_size=page_size,
        is_superuser=current_user.is_superuser,
        search_query=search_query,
    )
    return UserPageSchema.from_pagination(pagination)


@router.get("/users/me")
async def read_current_user(
    current_user: User = Depends(get_user(is_active=True)),
) -> ReadUserSchema:
    return ReadUserSchema.model_validate(current_user, from_attributes=True)


@router.get("/users/{user_id}", dependencies=[Depends(get_user(is_active=True))])
async def read_user(
    user_id: int,
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> ReadUserSchema:
    user = await unit_of_work.user.read_by_id(user_id=user_id, is_active=True)
    return ReadUserSchema.model_validate(user, from_attributes=True)
