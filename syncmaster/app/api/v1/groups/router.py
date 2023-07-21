from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DatabaseProviderMarker
from app.api.services import get_user
from app.api.v1.groups.schemas import (
    GroupPageSchema,
    ReadGroupSchema,
    UpdateGroupSchema,
)
from app.api.v1.schemas import StatusResponseSchema
from app.api.v1.users.schemas import UserPageSchema
from app.db.models import User
from app.db.provider import DatabaseProvider
from app.exceptions import (
    ActionNotAllowed,
    AlreadyIsGroupMember,
    AlreadyIsNotGroupMember,
    EntityNotFound,
    GroupAdminNotFound,
    GroupAlreadyExists,
)

router = APIRouter(tags=["Groups"])


@router.get("/groups")
async def get_groups(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> GroupPageSchema:
    pagination = await holder.group.paginate(
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return GroupPageSchema.from_pagination(pagination=pagination)


@router.post("/groups", dependencies=[Depends(get_user(is_superuser=True))])
async def create_group(
    group_data: UpdateGroupSchema,
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadGroupSchema:
    try:
        group = await holder.group.create(
            name=group_data.name,
            description=group_data.description,
            admin_id=group_data.admin_id,
        )
    except GroupAdminNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Admin not found"
        ) from e
    except GroupAlreadyExists as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group name already taken",
        ) from e
    return ReadGroupSchema.from_orm(group)


@router.get("/groups/{group_id}")
async def read_group(
    group_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadGroupSchema:
    try:
        group = await holder.group.read_by_id(
            group_id=group_id,
            is_superuser=current_user.is_superuser,
            current_user_id=current_user.id,
        )
    except EntityNotFound as e:
        raise HTTPException(status_code=404, detail="Group not found") from e
    return ReadGroupSchema.from_orm(group)


@router.post("/groups/{group_id}")
async def update_group(
    group_id: int,
    group_data: UpdateGroupSchema,
    current_user: User = Depends(get_user(is_active=True)),
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadGroupSchema:
    try:
        group = await holder.group.update(
            group_id=group_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            admin_id=group_data.admin_id,
            name=group_data.name,
            description=group_data.description,
        )
    except EntityNotFound as e:
        raise HTTPException(
            status_code=404,
            detail="Group not found",
        ) from e
    except GroupAdminNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin not found",
        ) from e
    except GroupAlreadyExists as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group name already taken",
        ) from e
    return ReadGroupSchema.from_orm(group)


@router.delete(
    "/groups/{group_id}", dependencies=[Depends(get_user(is_superuser=True))]
)
async def delete_group(
    group_id: int,
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    try:
        await holder.group.delete(group_id=group_id)
    except EntityNotFound as e:
        raise HTTPException(
            status_code=404,
            detail="Group not found",
        ) from e
    return StatusResponseSchema(ok=True, status_code=200, message="Group was deleted")


@router.get("/groups/{group_id}/users")
async def get_group_users(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> UserPageSchema:
    try:
        pagination = await holder.group.get_member_paginate(
            group_id=group_id,
            page=page,
            page_size=page_size,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        ) from e
    return UserPageSchema.from_pagination(pagination=pagination)


@router.post("/groups/{group_id}/users/{user_id}")
async def add_user_to_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    try:
        await holder.group.add_user(
            group_id=group_id,
            target_user_id=user_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        ) from e
    except AlreadyIsGroupMember as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already is group member",
        ) from e
    except ActionNotAllowed as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You have no power here"
        ) from e
    return StatusResponseSchema(
        ok=True, status_code=200, message="User was successfully added to group"
    )


@router.delete("/groups/{group_id}/users/{user_id}")
async def delete_user_from_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    holder: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    try:
        await holder.group.delete_user(
            group_id=group_id,
            target_user_id=user_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    except EntityNotFound as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        ) from e

    except AlreadyIsNotGroupMember as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already not group member",
        ) from e
    except ActionNotAllowed as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="You have no power here"
        ) from e
    return StatusResponseSchema(
        ok=True, status_code=200, message="User was successfully removed from group"
    )
