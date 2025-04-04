# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Sequence
from http.client import NO_CONTENT

from fastapi import APIRouter, Depends, Query
from pydantic import TypeAdapter

from syncmaster.db.models import Connection, ConnectionType, Transfer, User
from syncmaster.db.utils import Permission
from syncmaster.errors.registration import get_error_responses
from syncmaster.exceptions import ActionNotAllowedError
from syncmaster.exceptions.connection import (
    ConnectionAuthDataUpdateError,
    ConnectionDeleteError,
    ConnectionNotFoundError,
    ConnectionTypeUpdateError,
)
from syncmaster.exceptions.credentials import AuthDataNotFoundError
from syncmaster.exceptions.group import GroupNotFoundError
from syncmaster.schemas.v1.connection_types import CONNECTION_TYPES
from syncmaster.schemas.v1.connections.connection import (
    ConnectionCopySchema,
    ConnectionPageSchema,
    CreateConnectionSchema,
    ReadConnectionSchema,
    UpdateConnectionSchema,
)
from syncmaster.schemas.v1.page import MetaPageSchema
from syncmaster.server.services.get_user import get_user
from syncmaster.server.services.unit_of_work import UnitOfWork

router = APIRouter(tags=["Connections"], responses=get_error_responses())


@router.get("/connections")
async def read_connections(
    group_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=50, default=20),  # noqa: WPS432
    type: list[ConnectionType] | None = Query(None),
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
    search_query: str | None = Query(
        None,
        title="Search Query",
        description="full-text search for connections",
    ),
) -> ConnectionPageSchema:
    """Return connections in page format"""
    resource_role = await unit_of_work.connection.get_group_permission(
        user=current_user,
        group_id=group_id,
    )

    if resource_role == Permission.NONE:
        raise GroupNotFoundError

    connection_str_type = None if type is None else [ct.value for ct in type]

    pagination = await unit_of_work.connection.paginate(
        page=page,
        page_size=page_size,
        group_id=group_id,
        search_query=search_query,
        connection_type=connection_str_type,
    )
    items: list[ReadConnectionSchema] = []

    if pagination.items:
        credentials = await unit_of_work.credentials.read_bulk([item.id for item in pagination.items])
        items = [
            TypeAdapter(ReadConnectionSchema).validate_python(
                {
                    "id": item.id,
                    "group_id": item.group_id,
                    "name": item.name,
                    "description": item.description,
                    "type": item.type,
                    "data": item.data,
                    "auth_data": credentials.get(item.id, None),
                },
            )
            for item in pagination.items
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
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> ReadConnectionSchema:
    """Create new connection"""
    group_permission = await unit_of_work.connection.get_group_permission(
        user=current_user,
        group_id=connection_data.group_id,
    )
    if group_permission == Permission.NONE:
        raise GroupNotFoundError

    if group_permission < Permission.WRITE:
        raise ActionNotAllowedError

    async with unit_of_work:
        connection = await unit_of_work.connection.create(
            name=connection_data.name,
            type=connection_data.type,
            description=connection_data.description,
            group_id=connection_data.group_id,
            data=connection_data.data.model_dump(),
        )

        await unit_of_work.credentials.create(
            connection_id=connection.id,
            data=connection_data.auth_data.model_dump(),
        )

    credentials = await unit_of_work.credentials.read(connection.id)
    return TypeAdapter(ReadConnectionSchema).validate_python(
        {
            "id": connection.id,
            "group_id": connection.group_id,
            "name": connection.name,
            "description": connection.description,
            "type": connection.type,
            "data": connection.data,
            "auth_data": credentials,
        },
    )


@router.get("/connections/known_types", dependencies=[Depends(get_user(is_active=True))])
async def read_connection_types() -> list[str]:
    return CONNECTION_TYPES


@router.get("/connections/{connection_id}")
async def read_connection(
    connection_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> ReadConnectionSchema:
    resource_role = await unit_of_work.connection.get_resource_permission(
        user=current_user,
        resource_id=connection_id,
    )

    if resource_role == Permission.NONE:
        raise ConnectionNotFoundError

    connection = await unit_of_work.connection.read_by_id(connection_id)
    try:
        credentials = await unit_of_work.credentials.read(connection.id)
    except AuthDataNotFoundError:
        credentials = None

    return TypeAdapter(ReadConnectionSchema).validate_python(
        {
            "id": connection.id,
            "group_id": connection.group_id,
            "name": connection.name,
            "description": connection.description,
            "type": connection.type,
            "data": connection.data,
            "auth_data": credentials,
        },
    )


@router.put("/connections/{connection_id}")
async def update_connection(  # noqa: WPS217, WPS238
    connection_id: int,
    connection_data: UpdateConnectionSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> ReadConnectionSchema:
    resource_role = await unit_of_work.connection.get_resource_permission(
        user=current_user,
        resource_id=connection_id,
    )

    if resource_role == Permission.NONE:
        raise ConnectionNotFoundError

    if resource_role < Permission.WRITE:
        raise ActionNotAllowedError

    async with unit_of_work:
        existing_connection: Connection = await unit_of_work.connection.read_by_id(connection_id=connection_id)
        if connection_data.type != existing_connection.type:
            linked_transfers: Sequence[Transfer] = await unit_of_work.transfer.list_by_connection_id(connection_id)
            if linked_transfers:
                raise ConnectionTypeUpdateError

        existing_credentials = await unit_of_work.credentials.read(connection_id=connection_id)
        auth_data = connection_data.auth_data.model_dump()
        secret_field = connection_data.auth_data.secret_field

        if auth_data[secret_field] is None:
            if existing_credentials["type"] != auth_data["type"]:
                raise ConnectionAuthDataUpdateError

            auth_data[secret_field] = existing_credentials[secret_field]

        connection = await unit_of_work.connection.update(
            connection_id=connection_id,
            name=connection_data.name,
            type=connection_data.type,
            description=connection_data.description,
            data=connection_data.data.model_dump(),
        )
        await unit_of_work.credentials.update(
            connection_id=connection_id,
            data=auth_data,
        )

    credentials = await unit_of_work.credentials.read(connection_id)
    return TypeAdapter(ReadConnectionSchema).validate_python(
        {
            "id": connection.id,
            "group_id": connection.group_id,
            "name": connection.name,
            "description": connection.description,
            "type": connection.type,
            "data": connection.data,
            "auth_data": credentials,
        },
    )


@router.delete("/connections/{connection_id}", status_code=NO_CONTENT)
async def delete_connection(
    connection_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
):
    resource_role = await unit_of_work.connection.get_resource_permission(
        user=current_user,
        resource_id=connection_id,
    )
    if resource_role == Permission.NONE:
        raise ConnectionNotFoundError

    if resource_role < Permission.DELETE:
        raise ActionNotAllowedError

    connection = await unit_of_work.connection.read_by_id(connection_id)
    transfers = await unit_of_work.transfer.list_by_connection_id(connection.id)
    if transfers:
        raise ConnectionDeleteError(
            f"The connection has an associated transfers. Number of the connected transfers: {len(transfers)}",
        )

    async with unit_of_work:
        await unit_of_work.connection.delete(connection_id)


@router.post("/connections/{connection_id}/copy_connection")
async def copy_connection(  # noqa: WPS238
    connection_id: int,
    copy_connection_data: ConnectionCopySchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWork),
) -> ReadConnectionSchema:
    resource_role = await unit_of_work.connection.get_resource_permission(
        user=current_user,
        resource_id=connection_id,
    )
    if resource_role == Permission.NONE:
        raise ConnectionNotFoundError

    if copy_connection_data.remove_source and resource_role < Permission.DELETE:
        raise ActionNotAllowedError

    target_group_role = await unit_of_work.connection.get_group_permission(
        user=current_user,
        group_id=copy_connection_data.new_group_id,
    )
    if target_group_role == Permission.NONE:
        raise GroupNotFoundError

    if target_group_role < Permission.WRITE:
        raise ActionNotAllowedError

    async with unit_of_work:
        connection = await unit_of_work.connection.copy(
            connection_id=connection_id,
            new_group_id=copy_connection_data.new_group_id,
            new_name=copy_connection_data.new_name,
        )

        if copy_connection_data.remove_source:
            await unit_of_work.connection.delete(connection_id)

    return TypeAdapter(ReadConnectionSchema).validate_python(
        {
            "id": connection.id,
            "group_id": connection.group_id,
            "name": connection.name,
            "description": connection.description,
            "type": connection.type,
            "data": connection.data,
            "auth_data": None,
        },
    )
