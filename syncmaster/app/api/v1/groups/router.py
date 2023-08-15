from fastapi import APIRouter, Depends, Query

from app.api.deps import DatabaseProviderMarker
from app.api.services import get_user
from app.api.v1.groups.schemas import (
    GroupPageSchema,
    ReadGroupSchema,
    UpdateGroupSchema,
)
from app.api.v1.schemas import AclPageSchema, StatusResponseSchema
from app.api.v1.users.schemas import UserPageSchema
from app.db.models import User
from app.db.provider import DatabaseProvider

router = APIRouter(tags=["Groups"])


@router.get("/groups")
async def get_groups(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> GroupPageSchema:
    pagination = await provider.group.paginate(
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return GroupPageSchema.from_pagination(pagination=pagination)


@router.post("/groups", dependencies=[Depends(get_user(is_superuser=True))])
async def create_group(
    group_data: UpdateGroupSchema,
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadGroupSchema:
    group = await provider.group.create(
        name=group_data.name,
        description=group_data.description,
        admin_id=group_data.admin_id,
    )
    return ReadGroupSchema.from_orm(group)


@router.get("/groups/{group_id}")
async def read_group(
    group_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadGroupSchema:
    group = await provider.group.read_by_id(
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
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadGroupSchema:
    group = await provider.group.update(
        group_id=group_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        admin_id=group_data.admin_id,
        name=group_data.name,
        description=group_data.description,
    )
    return ReadGroupSchema.from_orm(group)


@router.delete(
    "/groups/{group_id}", dependencies=[Depends(get_user(is_superuser=True))]
)
async def delete_group(
    group_id: int,
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    await provider.group.delete(group_id=group_id)
    return StatusResponseSchema(ok=True, status_code=200, message="Group was deleted")


@router.get("/groups/{group_id}/users")
async def get_group_users(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> UserPageSchema:
    pagination = await provider.group.get_member_paginate(
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
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    await provider.group.add_user(
        group_id=group_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return StatusResponseSchema(
        ok=True, status_code=200, message="User was successfully added to group"
    )


@router.delete("/groups/{group_id}/users/{user_id}")
async def delete_user_from_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    await provider.group.delete_user(
        group_id=group_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return StatusResponseSchema(
        ok=True, status_code=200, message="User was successfully removed from group"
    )


@router.get("/groups/{group_id}/rules")
async def get_rules(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> AclPageSchema:
    pagination = await provider.group.paginate_rules(
        group_id=group_id,
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return AclPageSchema.from_pagination(pagination)
