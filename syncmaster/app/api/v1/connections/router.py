import asyncio
from typing import get_args

from fastapi import APIRouter, Depends, Query, status
from pydantic import SecretStr

from app.api.deps import UnitOfWorkMarker
from app.api.v1.connections.schemas import (
    ORACLE_TYPE,
    POSTGRES_TYPE,
    ConnectionCopySchema,
    ConnectionPageSchema,
    CreateConnectionSchema,
    ReadConnectionSchema,
    UpdateConnectionSchema,
)
from app.api.v1.schemas import MetaPageSchema, StatusResponseSchema
from app.db.models import User
from app.db.utils import Permission
from app.exceptions import ActionNotAllowed, AuthDataNotFound, GroupNotFound
from app.exceptions.connection import ConnectionDeleteException, ConnectionNotFound
from app.services import UnitOfWork, get_user

router = APIRouter(tags=["Connections"])


@router.get("/connections")
async def read_connections(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ConnectionPageSchema:
    """Return connections in page format"""
    resource_role = await unit_of_work.group.get_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_role == Permission.NONE:
        raise GroupNotFound

    pagination = await unit_of_work.connection.paginate(
        page=page,
        page_size=page_size,
        group_id=group_id,
    )
    items: list[ReadConnectionSchema] = []

    if pagination.items:
        creds = await asyncio.gather(
            *[unit_of_work.credentials.get_for_connection(connection_id=item.id) for item in pagination.items]
        )
        items = [
            ReadConnectionSchema(
                id=item.id,
                group_id=item.group_id,
                name=item.name,
                description=item.description,
                auth_data=creds[n_item],
                data=item.data,
            )
            for n_item, item in enumerate(pagination.items)
        ]

    return ConnectionPageSchema(
        meta=MetaPageSchema(
            page=pagination.page,
            pages=pagination.pages,
            total=pagination.total,
            page_size=pagination.page_size,
            has_next=pagination.has_next,
            has_previous=pagination.has_previous,
            next_page=pagination.next_page,
            previous_page=pagination.previous_page,
        ),
        items=items,
    )


@router.post("/connections")
async def create_connection(
    connection_data: CreateConnectionSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadConnectionSchema:
    """Create new connection"""
    group_permission = await unit_of_work.group.get_permission(
        user=current_user,
        group_id=connection_data.group_id,
    )
    if group_permission == Permission.NONE:
        raise GroupNotFound

    if group_permission < Permission.WRITE:
        raise ActionNotAllowed

    data = connection_data.data.dict()
    auth_data = connection_data.auth_data.dict()

    # Trick to serialize SecretStr to JSON
    for k, v in auth_data.items():
        if isinstance(v, SecretStr):
            auth_data[k] = v.get_secret_value()
    async with unit_of_work:
        connection = await unit_of_work.connection.create(
            name=connection_data.name,
            description=connection_data.description,
            group_id=connection_data.group_id,
            data=data,
        )

        await unit_of_work.credentials.add_to_connection(
            connection_id=connection.id,
            data=auth_data,
        )

    return ReadConnectionSchema(
        id=connection.id,
        group_id=connection.group_id,
        name=connection.name,
        description=connection.description,
        data=connection.data,
        auth_data=auth_data,
    )


@router.get("/connections/known_types", dependencies=[Depends(get_user(is_active=True))])
async def read_connection_types() -> list[str]:
    return [get_args(type_)[0] for type_ in (ORACLE_TYPE, POSTGRES_TYPE)]


@router.get("/connections/{connection_id}")
async def read_connection(
    connection_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadConnectionSchema:
    resource_role = await unit_of_work.connection.get_permission(
        user=current_user,
        resource_id=connection_id,
    )

    if resource_role == Permission.NONE:
        raise ConnectionNotFound

    connection = await unit_of_work.connection.read_by_id(connection_id=connection_id)

    try:
        credentials = await unit_of_work.credentials.get_for_connection(
            connection_id=connection.id,
        )
    except AuthDataNotFound:
        credentials = None

    return ReadConnectionSchema(
        id=connection.id,
        group_id=connection.group_id,
        name=connection.name,
        description=connection.description,
        data=connection.data,
        auth_data=credentials,
    )


@router.patch("/connections/{connection_id}")
async def update_connection(
    connection_id: int,
    connection_data: UpdateConnectionSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadConnectionSchema:
    resource_role = await unit_of_work.connection.get_permission(
        user=current_user,
        resource_id=connection_id,
    )

    if resource_role == Permission.NONE:
        raise ConnectionNotFound

    if resource_role < Permission.WRITE:
        raise ActionNotAllowed

    async with unit_of_work:
        connection = await unit_of_work.connection.update(
            connection_id=connection_id,
            name=connection_data.name,
            description=connection_data.description,
            connection_data=connection_data.data.dict(exclude={"auth_data"}) if connection_data.data else {},
        )

        if connection_data.auth_data:
            await unit_of_work.credentials.update(
                connection_id=connection_id,
                credential_data=connection_data.auth_data.dict(),
            )

    auth_data = await unit_of_work.credentials.get_for_connection(connection_id)

    return ReadConnectionSchema(
        id=connection.id,
        group_id=connection.group_id,
        name=connection.name,
        description=connection.description,
        data=connection.data,
        auth_data={
            "type": auth_data["type"],
            "user": auth_data["user"],
        },
    )


@router.delete("/connections/{connection_id}")
async def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    resource_role = await unit_of_work.connection.get_permission(
        user=current_user,
        resource_id=connection_id,
    )

    if resource_role == Permission.NONE:
        raise ConnectionNotFound

    if resource_role < Permission.DELETE:
        raise ActionNotAllowed

    connection = await unit_of_work.connection.read_by_id(connection_id=connection_id)

    transfers = await unit_of_work.transfer.list_by_connection_id(conn_id=connection.id)
    async with unit_of_work:
        if not transfers:
            await unit_of_work.connection.delete(connection_id=connection_id)

            return StatusResponseSchema(
                ok=True,
                status_code=status.HTTP_200_OK,
                message="Connection was deleted",
            )

    raise ConnectionDeleteException(
        f"The connection has an associated transfers. Number of the connected transfers: {len(transfers)}",
    )


@router.post("/connections/{connection_id}/copy_connection")
async def copy_connection(
    connection_id: int,
    copy_connection_data: ConnectionCopySchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    target_source_rules = await asyncio.gather(
        unit_of_work.connection.get_permission(
            user=current_user,
            resource_id=connection_id,
        ),
        unit_of_work.group.get_permission(
            user=current_user,
            group_id=copy_connection_data.new_group_id,
        ),
    )
    resource_role, target_group_role = target_source_rules

    if resource_role == Permission.NONE:
        raise ConnectionNotFound

    if target_group_role == Permission.NONE:
        raise GroupNotFound

    if target_group_role < Permission.WRITE:
        raise ActionNotAllowed

    if copy_connection_data.remove_source and resource_role < Permission.DELETE:
        raise ActionNotAllowed

    async with unit_of_work:
        await unit_of_work.connection.copy(
            connection_id=connection_id,
            new_group_id=copy_connection_data.new_group_id,
        )

        if copy_connection_data.remove_source:
            await unit_of_work.connection.delete(connection_id=connection_id)

    return StatusResponseSchema(
        ok=True,
        status_code=status.HTTP_200_OK,
        message="Connection was copied",
    )
