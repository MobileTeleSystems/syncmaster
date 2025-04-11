# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from http.client import NO_CONTENT

from fastapi import APIRouter, Depends, Query

from syncmaster.db.models import User
from syncmaster.db.models.group import GroupMemberRole
from syncmaster.db.utils import Permission
from syncmaster.errors.registration import get_error_responses
from syncmaster.exceptions import ActionNotAllowedError
from syncmaster.exceptions.group import AlreadyIsGroupOwnerError, GroupNotFoundError
from syncmaster.schemas.v1.groups import (
    AddUserSchema,
    CreateGroupSchema,
    GroupPageSchema,
    GroupWithUserRoleSchema,
    ReadGroupSchema,
    UpdateGroupSchema,
)
from syncmaster.schemas.v1.users import UserPageSchemaAsGroupMember
from syncmaster.server.services.get_user import get_user
from syncmaster.server.services.unit_of_work import UnitOfWork

router = APIRouter(tags=["Groups"], responses=get_error_responses())


@router.get("/groups")
async def read_groups(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=50, default=20),  # noqa: WPS432
    role: str | None = Query(default=None),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
    search_query: str | None = Query(
        None,
        title="Search Query",
        description="full-text search for groups",
    ),
) -> GroupPageSchema:
    if current_user.is_superuser:
        pagination = await unit_of_work.group.paginate_all(
            page=page,
            page_size=page_size,
            search_query=search_query,
        )
    else:
        pagination = await unit_of_work.group.paginate_for_user(
            page=page,
            page_size=page_size,
            current_user_id=current_user.id,
            role=role,
            search_query=search_query,
        )
    return GroupPageSchema.from_pagination(pagination=pagination)


@router.post("/groups")
async def create_group(
    group_data: CreateGroupSchema,
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
    current_user: User = Depends(get_user(is_active=True)),
) -> ReadGroupSchema:
    async with unit_of_work:
        group = await unit_of_work.group.create(
            name=group_data.name,
            description=group_data.description,
            owner_id=current_user.id,
        )
    return ReadGroupSchema.model_validate(group, from_attributes=True)


@router.get("/groups/{group_id}")
async def read_group(
    group_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> GroupWithUserRoleSchema:
    resource_role = await unit_of_work.group.get_group_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_role == Permission.NONE:
        raise GroupNotFoundError

    group = await unit_of_work.group.read_by_id(group_id=group_id)
    user_role = await unit_of_work.group.get_member_role(group_id=group_id, user_id=current_user.id)
    return GroupWithUserRoleSchema(
        data=ReadGroupSchema.model_validate(group, from_attributes=True),
        role=GroupMemberRole(user_role),
    )


@router.put("/groups/{group_id}")
async def update_group(  # noqa: WPS217
    group_id: int,
    group_data: UpdateGroupSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
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
        group = await unit_of_work.group.read_by_id(group_id=group_id)
        previous_owner_id = group.owner_id

        group = await unit_of_work.group.update(
            group_id=group_id,
            owner_id=group_data.owner_id,
            name=group_data.name,
            description=group_data.description,
        )

        if previous_owner_id != group_data.owner_id:
            new_owner_user_group = await unit_of_work.group.get_user_group(
                group_id=group_id,
                user_id=group_data.owner_id,
            )
            if new_owner_user_group:
                await unit_of_work.group.delete_user(group_id=group_id, target_user_id=group_data.owner_id)

            await unit_of_work.group.add_user(
                group_id=group_id,
                new_user_id=previous_owner_id,
                role=GroupMemberRole.Guest,
            )
    return ReadGroupSchema.model_validate(group, from_attributes=True)


@router.delete(
    "/groups/{group_id}",
    dependencies=[Depends(get_user(is_superuser=True))],
    status_code=NO_CONTENT,
)
async def delete_group(
    group_id: int,
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
):
    async with unit_of_work:
        await unit_of_work.group.delete(group_id=group_id)


@router.get("/groups/{group_id}/users")
async def read_group_users(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=50, default=20),  # noqa: WPS432
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
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


@router.put("/groups/{group_id}/users/{user_id}")
async def update_user_role_group(
    group_id: int,
    user_id: int,
    update_user_data: AddUserSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
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

    return AddUserSchema.model_validate(result, from_attributes=True)


@router.post("/groups/{group_id}/users/{user_id}", status_code=NO_CONTENT)
async def add_user_to_group(
    group_id: int,
    user_id: int,
    add_user_data: AddUserSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
):
    resource_rule = await unit_of_work.group.get_group_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_rule == Permission.NONE:
        raise GroupNotFoundError

    if resource_rule < Permission.DELETE:
        raise ActionNotAllowedError

    group = await unit_of_work.group.read_by_id(group_id=group_id)
    if group.owner_id == user_id:
        raise AlreadyIsGroupOwnerError

    async with unit_of_work:
        await unit_of_work.group.add_user(
            group_id=group_id,
            new_user_id=user_id,
            role=add_user_data.role,
        )


@router.delete("/groups/{group_id}/users/{user_id}", status_code=NO_CONTENT)
async def delete_user_from_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
):
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
