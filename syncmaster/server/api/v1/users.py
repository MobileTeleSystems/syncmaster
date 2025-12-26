# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import logging
from typing import Annotated

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
    current_user: Annotated[User, Depends(get_user())],
    unit_of_work: Annotated[UnitOfWork, Depends(UnitOfWork)],
    page: Annotated[int, Query(gt=0)] = 20,
    page_size: Annotated[int, Query(gt=0, le=50)] = 20,
    search_query: Annotated[str | None, Query(title="Search Query", description="fuzzy search for users")] = None,
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
    current_user: Annotated[User, Depends(get_user())],
) -> ReadUserSchema:
    return ReadUserSchema.model_validate(current_user, from_attributes=True)


@router.get("/users/{user_id}", dependencies=[Depends(get_user())])
async def read_user(
    user_id: int,
    unit_of_work: Annotated[UnitOfWork, Depends(UnitOfWork)],
) -> ReadUserSchema:
    user = await unit_of_work.user.read_by_id(user_id=user_id)
    return ReadUserSchema.model_validate(user, from_attributes=True)
