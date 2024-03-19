# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from fastapi import APIRouter, Depends, Query

from syncmaster.backend.api.deps import UnitOfWorkMarker
from syncmaster.backend.services import UnitOfWork, get_user
from syncmaster.db.models import User
from syncmaster.db.utils import Permission
from syncmaster.exceptions import ActionNotAllowedError
from syncmaster.exceptions.group import GroupNotFoundError
from syncmaster.schemas.v1.groups import (
    AddUserSchema,
    CreateGroupSchema,
    GroupPageSchema,
    ReadGroupSchema,
    UpdateGroupSchema,
)
from syncmaster.schemas.v1.status import StatusResponseSchema
from syncmaster.schemas.v1.users import UserPageSchemaAsGroupMember

router = APIRouter(tags=["Groups"])


@router.get("/groups")
async def read_groups(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> GroupPageSchema:
    if current_user.is_superuser:
        pagination = await unit_of_work.group.paginate_all(
            page=page,
            page_size=page_size,
        )
    else:
        pagination = await unit_of_work.group.paginate_for_user(
            page=page,
            page_size=page_size,
            current_user_id=current_user.id,
        )
    return GroupPageSchema.from_pagination(pagination=pagination)


@router.post("/groups")
async def create_group(
    group_data: CreateGroupSchema,
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
    current_user: User = Depends(get_user(is_active=True)),
) -> ReadGroupSchema:
    async with unit_of_work:
        group = await unit_of_work.group.create(
            name=group_data.name,
            description=group_data.description,
            owner_id=current_user.id,
        )
    return ReadGroupSchema.from_orm(group)


@router.get("/groups/{group_id}")
async def read_group(
    group_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadGroupSchema:
    resource_role = await unit_of_work.group.get_group_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_role == Permission.NONE:
        raise GroupNotFoundError

    group = await unit_of_work.group.read_by_id(group_id=group_id)
    return ReadGroupSchema.from_orm(group)


@router.patch("/groups/{group_id}")
async def update_group(
    group_id: int,
    group_data: UpdateGroupSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadGroupSchema:
    resource_rule = await unit_of_work.group.get_group_permission(
        user=current_user,
        group_id=group_id,
    )
    if resource_rule == Permission.NONE:
        raise GroupNotFoundError

    if resource_rule < Permission.DELETE:
        raise ActionNotAllowedError

    async with unit_of_work:
        group = await unit_of_work.group.update(
            group_id=group_id,
            owner_id=group_data.owner_id,
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
async def read_group_users(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> UserPageSchemaAsGroupMember:
    resource_role = await unit_of_work.group.get_group_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_role == Permission.NONE:
        raise GroupNotFoundError

    pagination = await unit_of_work.group.get_member_paginate(
        group_id=group_id,
        page=page,
        page_size=page_size,
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
    resource_rule = await unit_of_work.group.get_group_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_rule == Permission.NONE:
        raise GroupNotFoundError

    if resource_rule < Permission.DELETE:
        raise ActionNotAllowedError

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
    resource_rule = await unit_of_work.group.get_group_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_rule == Permission.NONE:
        raise GroupNotFoundError

    if resource_rule < Permission.DELETE:
        raise ActionNotAllowedError

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
    resource_rule = await unit_of_work.group.get_group_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_rule == Permission.NONE:
        raise GroupNotFoundError

    # User can delete himself from the group
    if user_id != current_user.id:
        if resource_rule < Permission.DELETE:
            raise ActionNotAllowedError

    async with unit_of_work:
        await unit_of_work.group.delete_user(
            group_id=group_id,
            target_user_id=user_id,
        )
    return StatusResponseSchema(ok=True, status_code=200, message="User was successfully removed from group")
