from fastapi import APIRouter, Depends, Query

from app.api.deps import UnitOfWorkMarker
from app.api.v1.groups.schemas import (
    AddUserSchema,
    GroupPageSchema,
    ReadGroupSchema,
    UpdateGroupSchema,
)
from app.api.v1.schemas import StatusResponseSchema
from app.api.v1.users.schemas import UserPageSchemaAsGroupMember
from app.db.models import User
from app.exceptions import ActionNotAllowed
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
    is_superuser = current_user.is_superuser
    cur_user_id = current_user.id

    group = await unit_of_work.group.read_by_id(
        group_id=group_id,
        is_superuser=is_superuser,
        current_user_id=cur_user_id,
    )
    if not (group.admin_id == cur_user_id or is_superuser):
        raise ActionNotAllowed

    async with unit_of_work:
        group = await unit_of_work.group.update(
            group_id=group_id,
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
) -> UserPageSchemaAsGroupMember:
    pagination = await unit_of_work.group.get_member_paginate(
        group_id=group_id,
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return UserPageSchemaAsGroupMember.from_pagination(pagination=pagination)


@router.patch("/groups/{group_id}/users/{user_id}")
async def update_user_role_group(
    group_id: int,
    user_id: int,
    update_user_data: AddUserSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> AddUserSchema:
    is_superuser = current_user.is_superuser
    cur_user_id = current_user.id

    group = await unit_of_work.group.read_by_id(
        group_id=group_id,
        is_superuser=is_superuser,
        current_user_id=cur_user_id,
    )
    if not is_superuser and not group.admin_id == cur_user_id:
        raise ActionNotAllowed

    async with unit_of_work:
        result = await unit_of_work.group.update_member_role(
            group_id=group_id,
            user_id=user_id,
            role=update_user_data.role,
        )

    return AddUserSchema.from_orm(result)


@router.post("/groups/{group_id}/users/{user_id}")
async def add_user_to_group(
    group_id: int,
    user_id: int,
    add_user_data: AddUserSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    is_superuser = current_user.is_superuser
    cur_user_id = current_user.id

    group = await unit_of_work.group.read_by_id(
        group_id=group_id,
        is_superuser=is_superuser,
        current_user_id=cur_user_id,
    )

    if not (group.admin_id == cur_user_id or is_superuser):
        raise ActionNotAllowed

    async with unit_of_work:
        await unit_of_work.group.add_user(
            group_id=group_id,
            new_user_id=user_id,
            role=add_user_data.role,
        )
    return StatusResponseSchema(
        ok=True,
        status_code=200,
        message="User was successfully added to group",
    )


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
