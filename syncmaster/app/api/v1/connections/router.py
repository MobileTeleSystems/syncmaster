from typing import get_args

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import SecretStr

from app.api.deps import DatabaseProviderMarker
from app.api.services import get_user
from app.api.v1.connections.schemas import (
    ORACLE_TYPE,
    POSTGRES_TYPE,
    ConnectionCopySchema,
    ConnectionPageSchema,
    CreateConnectionSchema,
    ReadConnectionSchema,
    UpdateConnectionSchema,
)
from app.api.v1.schemas import ReadAclSchema, SetRuleSchema, StatusResponseSchema
from app.db.models import Rule, User
from app.db.provider import DatabaseProvider
from app.exceptions import ActionNotAllowed

router = APIRouter(tags=["Connections"])


@router.get("/connections")
async def read_connections(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    user_id: int | None = None,
    group_id: int | None = None,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ConnectionPageSchema:
    """Return connections in page format"""
    if user_id and group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have to set user_id or group, or none. Not both at once",
        )
    pagination = await provider.connection.paginate(
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        group_id=group_id,
        user_id=user_id,
    )
    return ConnectionPageSchema.from_pagination(pagination=pagination)


@router.post("/connections")
async def create_connection(
    connection_data: CreateConnectionSchema,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadConnectionSchema:
    """Create new connection"""
    if not current_user.is_superuser:
        if connection_data.user_id and current_user.id != connection_data.user_id:
            raise ActionNotAllowed
        if connection_data.group_id:
            is_member = await provider.group.is_member(
                connection_data.group_id, current_user.id
            )
            is_admin = await provider.group.is_admin(
                connection_data.group_id, current_user.id
            )
            if not is_member and not is_admin:
                raise ActionNotAllowed
    else:
        is_member = False
    data = connection_data.data.dict()
    auth_data = connection_data.auth_data.dict()

    # Trick to serialize SecretStr to JSON
    for k, v in auth_data.items():
        if isinstance(v, SecretStr):
            auth_data[k] = v.get_secret_value()
    connection = await provider.connection.create(
        name=connection_data.name,
        description=connection_data.description,
        user_id=connection_data.user_id,
        group_id=connection_data.group_id,
        data=data,
        auth_data=auth_data,
    )
    if connection_data.group_id is not None and is_member:
        await provider.connection.add_or_update_rule(
            connection_id=connection.id,
            current_user_id=current_user.id,
            is_superuser=True,
            target_user_id=current_user.id,
            rule=Rule.DELETE,
        )
    return ReadConnectionSchema.from_orm(connection)


@router.get(
    "/connections/known_types", dependencies=[Depends(get_user(is_active=True))]
)
async def read_connection_types() -> list[str]:
    return [get_args(type_)[0] for type_ in (ORACLE_TYPE, POSTGRES_TYPE)]


@router.get("/connections/{connection_id}")
async def read_connection(
    connection_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadConnectionSchema:
    connection = await provider.connection.read_by_id(
        connection_id=connection_id,
        is_superuser=current_user.is_superuser,
        current_user_id=current_user.id,
    )
    return ReadConnectionSchema.from_orm(connection)


@router.patch("/connections/{connection_id}")
async def update_connection(
    connection_id: int,
    connection_data: UpdateConnectionSchema,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadConnectionSchema:
    connection = await provider.connection.update(
        connection_id=connection_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        name=connection_data.name,
        description=connection_data.description,
        connection_data=connection_data.data.dict() if connection_data.data else {},
    )
    return ReadConnectionSchema.from_orm(connection)


@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    await provider.connection.delete(
        connection_id=connection_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return StatusResponseSchema(
        ok=True, status_code=status.HTTP_200_OK, message="Connection was deleted"
    )


@router.post("/connections/{connection_id}/copy_connection")
async def copy_connection(
    connection_id: int,
    new_owner_data: ConnectionCopySchema,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    await provider.connection.copy_connection(
        connection_id=connection_id,
        new_group_id=new_owner_data.new_group_id,
        new_user_id=new_owner_data.new_user_id,
        remove_source=new_owner_data.remove_source,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return StatusResponseSchema(
        ok=True,
        status_code=status.HTTP_200_OK,
        message="Connection was copied.",
    )


@router.post("/connections/{connection_id}/rules")
async def add_or_update_rule(
    connection_id: int,
    rule_data: SetRuleSchema,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadAclSchema:
    """Add rule for user on connection in group or update if exists"""
    acl = await provider.connection.add_or_update_rule(
        connection_id=connection_id,
        rule=rule_data.rule,
        target_user_id=rule_data.user_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return ReadAclSchema.from_orm(acl)


@router.delete("/connections/{connection_id}/rules/{user_id}")
async def delete_rule(
    connection_id: int,
    user_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    """Delete rule for user on connection in group if exists"""
    await provider.connection.delete_rule(
        connection_id=connection_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return StatusResponseSchema(
        ok=True, status_code=status.HTTP_200_OK, message="Rule was deleted"
    )
