# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from syncmaster.exceptions import ActionNotAllowedError, SyncmasterError
from syncmaster.exceptions.connection import (
    ConnectionDeleteError,
    ConnectionNotFoundError,
    ConnectionOwnerError,
    DuplicatedConnectionNameError,
)
from syncmaster.exceptions.credentials import AuthDataNotFoundError
from syncmaster.exceptions.group import (
    AlreadyIsGroupMemberError,
    AlreadyIsNotGroupMemberError,
    GroupAdminNotFoundError,
    GroupAlreadyExistsError,
    GroupNotFoundError,
)
from syncmaster.exceptions.queue import (
    DifferentTransferAndQueueGroupError,
    QueueDeleteError,
    QueueNotFoundError,
)
from syncmaster.exceptions.run import (
    CannotConnectToTaskQueueError,
    CannotStopRunError,
    RunNotFoundError,
)
from syncmaster.exceptions.transfer import (
    DifferentTransferAndConnectionsGroupsError,
    DifferentTypeConnectionsAndParamsError,
    DuplicatedTransferNameError,
    TransferNotFoundError,
    TransferOwnerError,
)
from syncmaster.exceptions.user import UsernameAlreadyExistsError, UserNotFoundError
from syncmaster.schemas.v1.status import StatusResponseSchema

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    return exception_json_response(status_code=exc.status_code, detail=exc.detail)


async def syncmsater_exception_handler(request: Request, exc: SyncmasterError):
    if isinstance(exc, AuthDataNotFoundError):
        return exception_json_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Credentials not found. {exc.message}",
        )

    if isinstance(exc, ConnectionDeleteError):
        return exception_json_response(status_code=status.HTTP_409_CONFLICT, detail=exc.message)

    if isinstance(exc, ActionNotAllowedError):
        return exception_json_response(status_code=status.HTTP_403_FORBIDDEN, detail="You have no power here")

    if isinstance(exc, GroupNotFoundError):
        return exception_json_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    if isinstance(exc, RunNotFoundError):
        return exception_json_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Run not found",
        )

    if isinstance(exc, QueueNotFoundError):
        return exception_json_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Queue not found",
        )

    if isinstance(exc, GroupAdminNotFoundError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin not found",
        )
    if isinstance(exc, GroupAlreadyExistsError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group name already taken",
        )

    if isinstance(exc, AlreadyIsNotGroupMemberError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already is not group member",
        )

    if isinstance(exc, AlreadyIsGroupMemberError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already is group member",
        )

    if isinstance(exc, UserNotFoundError):
        return exception_json_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if isinstance(exc, UsernameAlreadyExistsError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken",
        )

    if isinstance(exc, ConnectionNotFoundError):
        return exception_json_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    if isinstance(exc, ConnectionOwnerError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create connection with that user_id and group_id values",
        )

    if isinstance(exc, TransferNotFoundError):
        return exception_json_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found",
        )

    if isinstance(exc, TransferOwnerError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot create transfer with that group_id value",
        )

    if isinstance(exc, DifferentTransferAndConnectionsGroupsError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Connections should belong to the transfer group",
        )

    if isinstance(exc, DifferentTransferAndQueueGroupError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Queue should belong to the transfer group",
        )

    if isinstance(exc, DifferentTypeConnectionsAndParamsError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=exc.message,
        )

    if isinstance(exc, QueueDeleteError):
        return exception_json_response(
            status_code=status.HTTP_409_CONFLICT,
            detail=exc.message,
        )

    if isinstance(exc, DuplicatedConnectionNameError):
        return exception_json_response(
            status_code=status.HTTP_409_CONFLICT,
            detail="The connection name already exists in the target group, please specify a new one",
        )

    if isinstance(exc, DuplicatedTransferNameError):
        return exception_json_response(
            status_code=status.HTTP_409_CONFLICT,
            detail="The transfer name already exists in the target group, please specify a new one",
        )

    if isinstance(exc, CannotConnectToTaskQueueError):
        return exception_json_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Syncmaster not connected to task queue. Run {exc.run_id} was failed",
        )

    if isinstance(exc, CannotStopRunError):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot stop run {exc.run_id}. Current status is {exc.current_status}",
        )

    logger.exception("Got unhandled error")
    return exception_json_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail="Got unhandled exception. See logs",
    )


def exception_json_response(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content=StatusResponseSchema(
            ok=False,
            status_code=status_code,
            message=detail,
        ).dict(),
    )
