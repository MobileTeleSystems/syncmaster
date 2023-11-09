from fastapi import APIRouter, Depends, Query

from app.api.deps import UnitOfWorkMarker
from app.api.v1.groups.schemas import (
    GroupPageSchema,
    ReadGroupSchema,
    UpdateGroupSchema,
)
from app.api.v1.schemas import StatusResponseSchema
from app.api.v1.users.schemas import UserPageSchema
from app.db.models import User
from app.services import UnitOfWork, get_user

router = APIRouter(tags=["Groups"])


@router.get("/groups")
async def get_groups(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> GroupPageSchema:
    pagination = await unit_of_work.group.paginate(
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return GroupPageSchema.from_pagination(pagination=pagination)


@router.post("/groups", dependencies=[Depends(get_user(is_superuser=True))])
async def create_group(
    group_data: UpdateGroupSchema,
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadGroupSchema:
    async with unit_of_work:
        group = await unit_of_work.group.create(
            name=group_data.name,
            description=group_data.description,
            admin_id=group_data.admin_id,
        )
    return ReadGroupSchema.from_orm(group)


@router.get("/groups/{group_id}")
async def read_group(
    group_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadGroupSchema:
    group = await unit_of_work.group.read_by_id(
        group_id=group_id,
        is_superuser=current_user.is_superuser,
        current_user_id=current_user.id,
    )
    return ReadGroupSchema.from_orm(group)


@router.patch("/groups/{group_id}")
async def update_group(
    group_id: int,
    group_data: UpdateGroupSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadGroupSchema:
    async with unit_of_work:
        group = await unit_of_work.group.update(
            group_id=group_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            admin_id=group_data.admin_id,
            name=group_data.name,
            description=group_data.description,
        )
    return ReadGroupSchema.from_orm(group)


@router.delete("/groups/{group_id}", dependencies=[Depends(get_user(is_superuser=True))])
async def delete_group(
    group_id: int,
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    async with unit_of_work:
        await unit_of_work.group.delete(group_id=group_id)
    return StatusResponseSchema(ok=True, status_code=200, message="Group was deleted")


@router.get("/groups/{group_id}/users")
async def get_group_users(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> UserPageSchema:
    pagination = await unit_of_work.group.get_member_paginate(
        group_id=group_id,
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return UserPageSchema.from_pagination(pagination=pagination)


@router.post("/groups/{group_id}/users/{user_id}")
async def add_user_to_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    async with unit_of_work:
        await unit_of_work.group.add_user(
            group_id=group_id,
            target_user_id=user_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    return StatusResponseSchema(ok=True, status_code=200, message="User was successfully added to group")


@router.delete("/groups/{group_id}/users/{user_id}")
async def delete_user_from_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    async with unit_of_work:
        await unit_of_work.group.delete_user(
            group_id=group_id,
            target_user_id=user_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    return StatusResponseSchema(ok=True, status_code=200, message="User was successfully removed from group")
