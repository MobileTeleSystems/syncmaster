from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from kombu.exceptions import KombuError

from app.api.deps import UnitOfWorkMarker
from app.api.services import get_user
from app.api.services.unit_of_work import UnitOfWork
from app.api.v1.schemas import (
    AclPageSchema,
    ReadRuleSchema,
    SetRuleSchema,
    StatusCopyTransferResponseSchema,
    StatusResponseSchema,
)
from app.api.v1.transfers.schemas import (
    CopyTransferSchema,
    CreateTransferSchema,
    ReadRunSchema,
    ReadTransferSchema,
    RunPageSchema,
    TransferPageSchema,
    UpdateTransferSchema,
)
from app.db.models import Rule, Status, User
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
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> TransferPageSchema:
    """Return transfers in page format"""
    if user_id and group_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have to set user_id or group, or none. Not both at once",
        )
    pagination = await unit_of_work.transfer.paginate(
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
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
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
            await unit_of_work.group.is_member(transfer_data.group_id, current_user.id)
            or await unit_of_work.group.is_admin(
                transfer_data.group_id, current_user.id
            )
        )
    ):
        raise ActionNotAllowed
    target_connection = await unit_of_work.connection.read_by_id(
        connection_id=transfer_data.target_connection_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    source_connection = await unit_of_work.connection.read_by_id(
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
        is_member = await unit_of_work.group.is_member(
            transfer_data.group_id, current_user.id
        )

    async with unit_of_work:
        transfer = await unit_of_work.transfer.create(
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
            await unit_of_work.transfer.add_or_update_rule(
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
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadTransferSchema:
    """Return transfer data by transfer ID"""
    transfer = await unit_of_work.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    return ReadTransferSchema.from_orm(transfer)


@router.post("/transfers/{transfer_id}/copy_transfer")
async def copy_transfer(
    transfer_id: int,
    transfer_data: CopyTransferSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusCopyTransferResponseSchema:
    rule = Rule.DELETE if transfer_data.remove_source else Rule.READ
    transfer = await unit_of_work.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        rule=rule,
    )

    async with unit_of_work:
        copied_source_connection = await unit_of_work.connection.copy_connection(
            connection_id=transfer.source_connection_id,
            new_group_id=transfer_data.new_group_id,
            new_user_id=transfer_data.new_user_id,
            remove_source=transfer_data.remove_source,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )

        copied_target_connection = (
            copied_source_connection  # source and target are the same (it's possible ?)
        )

        if (
            transfer.source_connection_id != transfer.target_connection_id
        ):  # Source and target are not the same
            copied_target_connection = await unit_of_work.connection.copy_connection(
                connection_id=transfer.target_connection_id,
                new_group_id=transfer_data.new_group_id,
                new_user_id=transfer_data.new_user_id,
                remove_source=transfer_data.remove_source,
                current_user_id=current_user.id,
                is_superuser=current_user.is_superuser,
            )

        copied_transfer = await unit_of_work.transfer.copy_transfer(
            transfer_id=transfer_id,
            new_group_id=transfer_data.new_group_id,
            new_user_id=transfer_data.new_user_id,
            new_source_connection=copied_source_connection.id,
            new_target_connection=copied_target_connection.id,
            remove_source=transfer_data.remove_source,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )

    return StatusCopyTransferResponseSchema(
        ok=True,
        status_code=status.HTTP_200_OK,
        message="Transfer was copied.",
        source_connection_id=copied_source_connection.id,
        target_connection_id=copied_target_connection.id,
        copied_transfer_id=copied_transfer.id,
    )


@router.patch("/transfers/{transfer_id}")
async def update_transfer(
    transfer_id: int,
    transfer_data: UpdateTransferSchema,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadTransferSchema:
    transfer = await unit_of_work.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        rule=Rule.WRITE,
    )
    target_connection = await unit_of_work.connection.read_by_id(
        connection_id=transfer_data.target_connection_id
        or transfer.target_connection_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    source_connection = await unit_of_work.connection.read_by_id(
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

    async with unit_of_work:
        transfer = await unit_of_work.transfer.update(
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
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    async with unit_of_work:
        await unit_of_work.transfer.delete(
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
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadRuleSchema:
    rule = Rule.from_str(rule_data.rule)
    async with unit_of_work:
        acl = await unit_of_work.transfer.add_or_update_rule(
            transfer_id=transfer_id,
            rule=rule,
            target_user_id=rule_data.user_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
        )
    return ReadRuleSchema.from_acl(acl)


@router.delete("/transfers/{transfer_id}/rules/{user_id}")
async def delete_rule(
    transfer_id: int,
    user_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> StatusResponseSchema:
    """Delete rule for user on transfer in group if exists"""
    async with unit_of_work:
        await unit_of_work.transfer.delete_rule(
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
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> RunPageSchema:
    """Return runs of transfer with pagination"""
    await unit_of_work.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    pagination = await unit_of_work.run.paginate(
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
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadRunSchema:
    await unit_of_work.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    run = await unit_of_work.run.read_by_id(run_id=run_id)
    return ReadRunSchema.from_orm(run)


@router.post("/transfers/{transfer_id}/runs")
async def start_transfer(
    transfer_id: int,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadRunSchema:
    await unit_of_work.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        rule=Rule.READ,
    )
    try:
        await unit_of_work.transfer.read_by_id(
            transfer_id=transfer_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            rule=Rule.WRITE,
        )
    except TransferNotFound as e:
        raise ActionNotAllowed from e
    async with unit_of_work:
        run = await unit_of_work.run.create(transfer_id=transfer_id)
    try:
        celery.send_task("run_transfer_task", kwargs={"run_id": run.id})
    except KombuError as e:
        async with unit_of_work:
            run = await unit_of_work.run.update(
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
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> ReadRunSchema:
    await unit_of_work.transfer.read_by_id(
        transfer_id=transfer_id,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
    )
    try:
        await unit_of_work.transfer.read_by_id(
            transfer_id=transfer_id,
            current_user_id=current_user.id,
            is_superuser=current_user.is_superuser,
            rule=Rule.WRITE,
        )
    except TransferNotFound as e:
        raise ActionNotAllowed from e
    async with unit_of_work:
        run = await unit_of_work.run.stop(run_id=run_id)
        # TODO add immdiate stop transfer after stop Run
    return ReadRunSchema.from_orm(run)


@router.get("/transfers/{transfer_id}/rules")
async def get_rules(
    transfer_id: int,
    user_id: Annotated[int | None, Query()] = None,
    page: Annotated[int, Query(gt=0)] = 1,
    page_size: Annotated[int, Query(gt=0, le=200)] = 20,
    current_user: User = Depends(get_user(is_active=True)),
    unit_of_work: UnitOfWork = Depends(UnitOfWorkMarker),
) -> AclPageSchema:
    """Getting a list of users with their rights for a given transfer"""
    transfer = await unit_of_work.transfer.read_by_id(
        transfer_id=transfer_id,
        is_superuser=current_user.is_superuser,
        current_user_id=current_user.id,
    )
    group_id: int = transfer.group_id  # type: ignore[assignment]

    pagination = await unit_of_work.transfer.paginate_rules(
        object_id=transfer_id,
        group_id=group_id,
        page=page,
        page_size=page_size,
        current_user_id=current_user.id,
        is_superuser=current_user.is_superuser,
        user_id=user_id,
    )
    return AclPageSchema.from_pagination(pagination)
