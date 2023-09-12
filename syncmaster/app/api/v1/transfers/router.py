from fastapi import APIRouter, Depends, HTTPException, Query, status
from kombu.exceptions import KombuError

from app.api.deps import DatabaseProviderMarker
from app.api.services import get_user
from app.api.v1.schemas import ReadAclSchema, SetRuleSchema, StatusResponseSchema
from app.api.v1.transfers.schemas import (
    CreateTransferSchema,
    ReadRunSchema,
    ReadTransferSchema,
    RunPageSchema,
    TransferPageSchema,
    UpdateTransferSchema,
)
from app.db.models import Rule, Status, User
from app.db.provider import DatabaseProvider
from app.exceptions import (
    CannotConnectToTaskQueueError,
    DifferentConnectionsOwners,
    DifferentTypeConnectionsAndParams,
    TransferNotFound,
)
from app.exceptions.base import ActionNotAllowed
from app.tasks.config import celery

router = APIRouter(tags=["Transfers"])


@router.get("/transfers")
async def read_transfers(
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    user_id: int | None = None,
    group_id: int | None = None,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> TransferPageSchema:
    """Return transfers in page format"""
    if user_id and group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have to set user_id or group, or none. Not both at once",
        )
    pagination = await provider.transfer.paginate(
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        group_id=group_id,
        user_id=user_id,
    )
    return TransferPageSchema.from_pagination(pagination=pagination)


@router.post("/transfers")
async def create_transfer(
    transfer_data: CreateTransferSchema,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadTransferSchema:
    """Create new transfer"""
    if (
        not current_user.is_superuser
        and transfer_data.user_id is not None
        and current_user.id != transfer_data.user_id
    ):
        raise ActionNotAllowed
    if (
        not current_user.is_superuser
        and transfer_data.group_id is not None
        and not (
            await provider.group.is_member(transfer_data.group_id, current_user.id)
            or await provider.group.is_admin(transfer_data.group_id, current_user.id)
        )
    ):
        raise ActionNotAllowed
    target_connection = await provider.connection.read_by_id(
        connection_id=transfer_data.target_connection_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    source_connection = await provider.connection.read_by_id(
        connection_id=transfer_data.source_connection_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    if (target_connection.group_id, target_connection.user_id) != (
        source_connection.group_id,
        source_connection.user_id,
    ):
        raise DifferentConnectionsOwners
    if target_connection.data["type"] != transfer_data.target_params.type:
        raise DifferentTypeConnectionsAndParams(
            connection_type=target_connection.data["type"],
            conn="target",
            params_type=transfer_data.target_params.type,
        )

    if source_connection.data["type"] != transfer_data.source_params.type:
        raise DifferentTypeConnectionsAndParams(
            connection_type=source_connection.data["type"],
            conn="source",
            params_type=transfer_data.source_params.type,
        )
    is_member = False
    if transfer_data.group_id is not None and not current_user.is_superuser:
        is_member = await provider.group.is_member(
            transfer_data.group_id, current_user.id
        )

    transfer = await provider.transfer.create(
        user_id=transfer_data.user_id,
        group_id=transfer_data.group_id,
        name=transfer_data.name,
        description=transfer_data.description,
        target_connection_id=transfer_data.target_connection_id,
        source_connection_id=transfer_data.source_connection_id,
        source_params=transfer_data.source_params.dict(),
        target_params=transfer_data.target_params.dict(),
        strategy_params=transfer_data.strategy_params.dict(),
    )
    if transfer_data.group_id is not None and is_member:
        await provider.transfer.add_or_update_rule(
            transfer_id=transfer.id,
            current_user_id=current_user.id,
            is_superuser=True,
            target_user_id=current_user.id,
            rule=Rule.DELETE,
        )
    return ReadTransferSchema.from_orm(transfer)


@router.get("/transfers/{transfer_id}")
async def read_transfer(
    transfer_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadTransferSchema:
    """Return transfer data by transfer ID"""
    transfer = await provider.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return ReadTransferSchema.from_orm(transfer)


@router.patch("/transfers/{transfer_id}")
async def update_transfer(
    transfer_id: int,
    transfer_data: UpdateTransferSchema,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadTransferSchema:
    transfer = await provider.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        rule=Rule.WRITE,
    )
    target_connection = await provider.connection.read_by_id(
        connection_id=transfer_data.target_connection_id
        or transfer.target_connection_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    source_connection = await provider.connection.read_by_id(
        connection_id=transfer_data.source_connection_id
        or transfer.source_connection_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    if (target_connection.group_id, target_connection.user_id) != (
        source_connection.group_id,
        source_connection.user_id,
    ):
        raise DifferentConnectionsOwners
    if (
        transfer_data.target_params
        and target_connection.data["type"] != transfer_data.target_params.type
    ):
        raise DifferentTypeConnectionsAndParams(
            connection_type=target_connection.data["type"],
            conn="target",
            params_type=transfer_data.target_params.type,
        )

    if (
        transfer_data.source_params
        and source_connection.data["type"] != transfer_data.source_params.type
    ):
        raise DifferentTypeConnectionsAndParams(
            connection_type=source_connection.data["type"],
            conn="source",
            params_type=transfer_data.source_params.type,
        )
    transfer = await provider.transfer.update(
        transfer=transfer,
        name=transfer_data.name,
        description=transfer_data.description,
        target_connection_id=transfer_data.target_connection_id,
        source_connection_id=transfer_data.source_connection_id,
        source_params=transfer_data.source_params.dict()
        if transfer_data.source_params
        else {},
        target_params=transfer_data.target_params.dict()
        if transfer_data.target_params
        else {},
        strategy_params=transfer_data.strategy_params.dict()
        if transfer_data.strategy_params
        else {},
        is_scheduled=transfer_data.is_scheduled,
        schedule=transfer_data.schedule,
    )
    return ReadTransferSchema.from_orm(transfer)


@router.delete("/transfers/{transfer_id}")
async def delete_transfer(
    transfer_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    await provider.transfer.delete(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return StatusResponseSchema(
        ok=True, status_code=status.HTTP_200_OK, message="Transfer was deleted"
    )


@router.post("/transfers/{transfer_id}/rules")
async def add_or_update_rule(
    transfer_id: int,
    rule_data: SetRuleSchema,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadAclSchema:
    acl = await provider.transfer.add_or_update_rule(
        transfer_id=transfer_id,
        rule=rule_data.rule,
        target_user_id=rule_data.user_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return ReadAclSchema.from_orm(acl)


@router.delete("/transfers/{transfer_id}/rules/{user_id}")
async def delete_rule(
    transfer_id: int,
    user_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> StatusResponseSchema:
    """Delete rule for user on transfer in group if exists"""
    await provider.transfer.delete_rule(
        transfer_id=transfer_id,
        target_user_id=user_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return StatusResponseSchema(
        ok=True,
        status_code=status.HTTP_200_OK,
        message="Rule was deleted",
    )


@router.get("/transfers/{transfer_id}/runs")
async def read_runs(
    transfer_id: int,
    page: int = Query(gt=0, default=1),
    page_size: int = Query(gt=0, le=200, default=20),
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> RunPageSchema:
    """Return runs of transfer with pagination"""
    await provider.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    pagination = await provider.run.paginate(
        transfer_id=transfer_id,
        page=page,
        page_size=page_size,
    )
    return RunPageSchema.from_pagination(pagination=pagination)


@router.get("/transfers/{transfer_id}/runs/{run_id}")
async def read_run(
    transfer_id: int,
    run_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadRunSchema:
    await provider.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    run = await provider.run.read_by_id(run_id=run_id)
    return ReadRunSchema.from_orm(run)


@router.post("/transfers/{transfer_id}/runs")
async def start_transfer(
    transfer_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadRunSchema:
    await provider.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        rule=Rule.READ,
    )
    try:
        await provider.transfer.read_by_id(
            transfer_id=transfer_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            rule=Rule.WRITE,
        )
    except TransferNotFound as e:
        raise ActionNotAllowed from e
    run = await provider.run.create(transfer_id=transfer_id)
    try:
        celery.send_task("run_transfer_task", kwargs={"run_id": run.id})
    except KombuError as e:
        run = await provider.run.update(
            run_id=run.id,
            status=Status.FAILED,
        )
        raise CannotConnectToTaskQueueError(run_id=run.id) from e
    return ReadRunSchema.from_orm(run)


@router.post("/transfers/{transfer_id}/runs/{run_id}/stop")
async def stop_run(
    transfer_id: int,
    run_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    provider: DatabaseProvider = Depends(DatabaseProviderMarker),
) -> ReadRunSchema:
    await provider.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    try:
        await provider.transfer.read_by_id(
            transfer_id=transfer_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            rule=Rule.WRITE,
        )
    except TransferNotFound as e:
        raise ActionNotAllowed from e
    run = await provider.run.stop(run_id=run_id)
    # TODO add immdiate stop transfer after stop Run
    return ReadRunSchema.from_orm(run)
