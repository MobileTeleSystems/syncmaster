import asyncio
from typing import Annotated, get_args

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import SecretStr

from app.api.deps import UnitOfWorkMarker
from app.api.services import get_user
from app.api.services.unit_of_work import UnitOfWork
from app.api.v1.connections.schemas import (
    ORACLE_TYPE,
    POSTGRES_TYPE,
    ConnectionCopySchema,
    ConnectionPageSchema,
    CreateConnectionSchema,
    ReadConnectionSchema,
    UpdateConnectionSchema,
)
from app.api.v1.schemas import (
    AclPageSchema,
    MetaPageSchema,
    ReadRuleSchema,
    SetRuleSchema,
    StatusResponseSchema,
)
from app.db.models import Rule, User
from app.exceptions import ActionNotAllowed, AuthDataNotFound
from app.exceptions.connection import ConnectionDeleteException

router = APIRouter(tags=["Connections"])


@router.get("/connections")
async def read_connections(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    user_id: int | None = None,
    group_id: int | None = None,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ConnectionPageSchema:
    """Return connections in page format"""
    if user_id and group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have to set user_id or group, or none. Not both at once",
        )
    pagination = await unit_of_work.connection.paginate(
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        group_id=group_id,
        user_id=user_id,
    )

    items = []
    if pagination.items:
        creds = await asyncio.gather(
            *[
                unit_of_work.credentials.get_for_connection(connection_id=item.id)
                for item in pagination.items
            ]
        )

        items = [
            ReadConnectionSchema(
                id=item.id,
                user_id=item.user_id,
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
    if not current_user.is_superuser:
        if connection_data.user_id and current_user.id != connection_data.user_id:
            raise ActionNotAllowed
        if connection_data.group_id:
            is_member = await unit_of_work.group.is_member(
                connection_data.group_id, current_user.id
            )
            is_admin = await unit_of_work.group.is_admin(
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
    async with unit_of_work:
        connection = await unit_of_work.connection.create(
            name=connection_data.name,
            description=connection_data.description,
            user_id=connection_data.user_id,
            group_id=connection_data.group_id,
            data=data,
        )

        await unit_of_work.credentials.add_to_connection(
            connection_id=connection.id,
            data=auth_data,
        )

        if connection_data.group_id is not None and is_member:
            await unit_of_work.connection.add_or_update_rule(
                connection_id=connection.id,
                current_user_id=current_user.id,
                is_superuser=True,
                target_user_id=current_user.id,
                rule=Rule.DELETE,
            )

    return ReadConnectionSchema(
        id=connection.id,
        user_id=connection.user_id,
        group_id=connection.group_id,
        name=connection.name,
        description=connection.description,
        data=connection.data,
        auth_data=auth_data,
    )


@router.get(
    "/connections/known_types", dependencies=[Depends(get_user(is_active=True))]
)
async def read_connection_types() -> list[str]:
    return [get_args(type_)[0] for type_ in (ORACLE_TYPE, POSTGRES_TYPE)]


@router.get("/connections/{connection_id}")
async def read_connection(
    connection_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadConnectionSchema:
    connection = await unit_of_work.connection.read_by_id(
        connection_id=connection_id,
        is_superuser=current_user.is_superuser,
        current_user_id=current_user.id,
    )
    try:
        credentials = await unit_of_work.credentials.get_for_connection(
            connection_id=connection.id
        )
    except AuthDataNotFound:
        credentials = None

    return ReadConnectionSchema(
        id=connection.id,
        user_id=connection.user_id,
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
    async with unit_of_work:
        connection = await unit_of_work.connection.update(
            connection_id=connection_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            name=connection_data.name,
            description=connection_data.description,
            connection_data=connection_data.data.dict(exclude={"auth_data"})
            if connection_data.data
            else {},
        )

        if connection_data.auth_data:
            await unit_of_work.credentials.update(
                connection_id=connection_id,
                credential_data=connection_data.auth_data.dict(),
            )

    auth_data = await unit_of_work.credentials.get_for_connection(connection_id)

    return ReadConnectionSchema(
        id=connection.id,
        user_id=connection.user_id,
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
    connection = await unit_of_work.connection.read_by_id(
        connection_id=connection_id,
        is_superuser=current_user.is_superuser,
        current_user_id=current_user.id,
    )

    transfers = await unit_of_work.transfer.list_by_connection_id(conn_id=connection.id)
    async with unit_of_work:
        if not transfers:
            await unit_of_work.connection.delete(
                connection_id=connection_id,
                current_user_id=current_user.id,
                is_superuser=current_user.is_superuser,
            )

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
    new_owner_data: ConnectionCopySchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    async with unit_of_work:
        await unit_of_work.connection.copy_connection(
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
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadRuleSchema:
    """Add rule for user on connection in group or update if exists"""
    rule = Rule.from_str(rule_data.rule)
    async with unit_of_work:
        acl = await unit_of_work.connection.add_or_update_rule(
            connection_id=connection_id,
            rule=rule,
            target_user_id=rule_data.user_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    return ReadRuleSchema.from_acl(acl)


@router.delete("/connections/{connection_id}/rules/{user_id}")
async def delete_rule(
    connection_id: int,
    user_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    """Delete rule for user on connection in group if exists"""
    async with unit_of_work:
        await unit_of_work.connection.delete_rule(
            connection_id=connection_id,
            target_user_id=user_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    return StatusResponseSchema(
        ok=True, status_code=status.HTTP_200_OK, message="Rule was deleted"
    )


@router.get("/connections/{connection_id}/rules")
async def get_rules(
    connection_id: int,
    user_id: Annotated[int | None, Query()] = None,
    page: Annotated[int, Query(gt=0)] = 1,
    page_size: Annotated[int, Query(gt=0, le=200)] = 20,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> AclPageSchema:
    """Getting a list of users with their rights for a given connection"""
    connection = await unit_of_work.connection.read_by_id(
        connection_id=connection_id,
        is_superuser=current_user.is_superuser,
        current_user_id=current_user.id,
    )
    group_id: int = connection.group_id  # type: ignore[assignment]

    pagination = await unit_of_work.connection.paginate_rules(
        object_id=connection_id,
        group_id=group_id,
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        user_id=user_id,
    )
    return AclPageSchema.from_pagination(pagination)
