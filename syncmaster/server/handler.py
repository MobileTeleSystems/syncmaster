# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import http
import logging

from fastapi import HTTPException, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from syncmaster.errors.base import APIErrorSchema, BaseErrorSchema
from syncmaster.errors.registration import get_response_for_exception
from syncmaster.exceptions import ActionNotAllowedError, SyncmasterError
from syncmaster.exceptions.auth import AuthorizationError
from syncmaster.exceptions.connection import (
    ConnectionAuthDataUpdateError,
    ConnectionDeleteError,
    ConnectionNotFoundError,
    ConnectionOwnerError,
    ConnectionTypeUpdateError,
    DuplicatedConnectionNameError,
)
from syncmaster.exceptions.credentials import AuthDataNotFoundError
from syncmaster.exceptions.group import (
    AlreadyIsGroupMemberError,
    AlreadyIsGroupOwnerError,
    AlreadyIsNotGroupMemberError,
    GroupAlreadyExistsError,
    GroupNotFoundError,
)
from syncmaster.exceptions.queue import (
    DifferentTransferAndQueueGroupError,
    DuplicatedQueueNameError,
    QueueDeleteError,
    QueueNotFoundError,
)
from syncmaster.exceptions.redirect import RedirectException
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

logger = logging.getLogger(__name__)

# TODO: add unit tests


def http_exception_handler(request: Request, exc: HTTPException) -> Response:
    content = BaseErrorSchema(
        code=http.HTTPStatus(exc.status_code).name.lower(),
        message=exc.detail,
        details=None,
    )
    return exception_json_response(
        status=exc.status_code,
        content=content,
        headers=exc.headers,  # type: ignore[arg-type]
    )


def unknown_exception_handler(request: Request, exc: Exception) -> Response:
    logger.exception("Got unhandled error: %s", exc, exc_info=exc)

    details = None
    if request.app.debug:
        details = exc.args

    content = BaseErrorSchema(
        code="unknown",
        message="Got unhandled exception. Please contact support",
        details=details,
    )
    return exception_json_response(
        status=http.HTTPStatus.INTERNAL_SERVER_ERROR.value,
        content=content,
        # https://github.com/snok/asgi-correlation-id#exception-handling
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> Response:
    response = get_response_for_exception(ValidationError)
    if not response:
        return unknown_exception_handler(request, exc)

    # code and message are defined within class implementation
    errors = []
    for error in exc.errors():
        # pydantic Error classes are not serializable, drop it
        error.get("ctx", {}).pop("error", None)
        errors.append(error)

    content = response.schema(  # type: ignore[call-arg]
        details=errors,
    )
    return exception_json_response(
        status=response.status,
        content=content,
    )


async def syncmsater_exception_handler(request: Request, exc: SyncmasterError):  # noqa: WPS231, WPS212
    response = get_response_for_exception(SyncmasterError)
    if not response:
        return unknown_exception_handler(request, exc)

    content = response.schema(  # type: ignore[call-arg]
        message=exc.message if hasattr(exc, "message") else "",
    )
    if isinstance(exc, AuthDataNotFoundError):
        content.code = "not_found"
        content.message = f"Credentials not found. {exc.message}"
        return exception_json_response(
            status=status.HTTP_404_NOT_FOUND,
            content=content,
        )

    if isinstance(exc, RedirectException):
        return RedirectResponse(url=exc.redirect_url)

    if isinstance(exc, AuthorizationError):
        content.code = "unauthorized"
        content.message = "Not authenticated"
        return exception_json_response(status=status.HTTP_401_UNAUTHORIZED, content=content)

    if isinstance(exc, ConnectionDeleteError):
        content.code = "conflict"
        return exception_json_response(status=status.HTTP_409_CONFLICT, content=content)

    if isinstance(exc, ActionNotAllowedError):
        content.code = "forbidden"
        content.message = "You have no power here"
        return exception_json_response(status=status.HTTP_403_FORBIDDEN, content=content)

    if isinstance(exc, GroupNotFoundError):
        content.code = "not_found"
        content.message = "Group not found"
        return exception_json_response(
            status=status.HTTP_404_NOT_FOUND,
            content=content,
        )

    if isinstance(exc, RunNotFoundError):
        content.code = "not_found"
        content.message = "Run not found"
        return exception_json_response(
            status=status.HTTP_404_NOT_FOUND,
            content=content,
        )

    if isinstance(exc, QueueNotFoundError):
        content.code = "not_found"
        content.message = "Queue not found"
        return exception_json_response(
            status=status.HTTP_404_NOT_FOUND,
            content=content,
        )

    if isinstance(exc, GroupAlreadyExistsError):
        content.code = "conflict"
        content.message = "Group name already taken"
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, AlreadyIsNotGroupMemberError):
        content.code = "conflict"
        content.message = "User already is not group member"
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, AlreadyIsGroupMemberError):
        content.code = "conflict"
        content.message = "User already is group member"
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, AlreadyIsGroupOwnerError):
        content.code = "conflict"
        content.message = "User already is group owner"
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, UserNotFoundError):
        content.code = "not_found"
        content.message = "User not found"
        return exception_json_response(
            status=status.HTTP_404_NOT_FOUND,
            content=content,
        )

    if isinstance(exc, UsernameAlreadyExistsError):
        content.code = "conflict"
        content.message = "Username is already taken"
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, ConnectionNotFoundError):
        content.code = "not_found"
        content.message = "Connection not found"
        return exception_json_response(
            status=status.HTTP_404_NOT_FOUND,
            content=content,
        )

    if isinstance(exc, ConnectionOwnerError):
        content.message = "Cannot create connection with that user_id and group_id values"
        return exception_json_response(
            status=status.HTTP_400_BAD_REQUEST,
            content=content,
        )

    if isinstance(exc, TransferNotFoundError):
        content.code = "not_found"
        content.message = "Transfer not found"
        return exception_json_response(
            status=status.HTTP_404_NOT_FOUND,
            content=content,
        )

    if isinstance(exc, TransferOwnerError):
        content.message = "Cannot create transfer with that group_id value"
        return exception_json_response(
            status=status.HTTP_400_BAD_REQUEST,
            content=content,
        )

    if isinstance(exc, ConnectionTypeUpdateError):
        content.code = "conflict"
        content.message = "You cannot update the connection type of a connection already associated with a transfer."
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, ConnectionAuthDataUpdateError):
        content.code = "conflict"
        content.message = "You cannot update the connection auth type without providing a new secret value."
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, DifferentTransferAndConnectionsGroupsError):
        content.message = "Connections should belong to the transfer group"
        return exception_json_response(
            status=status.HTTP_400_BAD_REQUEST,
            content=content,
        )

    if isinstance(exc, DifferentTransferAndQueueGroupError):
        content.message = "Queue should belong to the transfer group"
        return exception_json_response(
            status=status.HTTP_400_BAD_REQUEST,
            content=content,
        )

    if isinstance(exc, DifferentTypeConnectionsAndParamsError):
        return exception_json_response(
            status=status.HTTP_400_BAD_REQUEST,
            content=content,
        )

    if isinstance(exc, QueueDeleteError):
        content.code = "conflict"
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, DuplicatedConnectionNameError):
        content.code = "conflict"
        content.message = "The connection name already exists in the target group, please specify a new one"
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, DuplicatedTransferNameError):
        content.code = "conflict"
        content.message = "The transfer name already exists in the target group, please specify a new one"
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, DuplicatedQueueNameError):
        content.code = "conflict"
        content.message = "The queue name already exists in the target group, please specify a new one"
        return exception_json_response(
            status=status.HTTP_409_CONFLICT,
            content=content,
        )

    if isinstance(exc, CannotConnectToTaskQueueError):
        content.code = "service_unavaliable"
        content.message = f"Syncmaster not connected to task queue. Run {exc.run_id} was failed"
        return exception_json_response(
            status=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=content,
        )

    if isinstance(exc, CannotStopRunError):
        content.message = f"Cannot stop run {exc.run_id}. Current status is {exc.current_status}"
        return exception_json_response(
            status=status.HTTP_400_BAD_REQUEST,
            content=content,
        )

    logger.exception("Got unhandled error")
    content.code = "unknown"
    content.message = "Got unhandled exception. See logs"
    return exception_json_response(
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content,
    )


def exception_json_response(
    status: int,
    content: BaseErrorSchema,
    headers: dict[str, str] | None = None,
) -> Response:
    content_type = type(content)
    error_schema = APIErrorSchema[content_type]  # type: ignore[valid-type]
    return Response(
        status_code=status,
        content=error_schema(error=content).model_dump_json(by_alias=True),
        media_type="application/json",
        headers=headers,
    )
