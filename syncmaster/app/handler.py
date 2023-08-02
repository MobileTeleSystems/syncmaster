import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.schemas import StatusResponseSchema
from app.exceptions import (
    AclNotFound,
    ActionNotAllowed,
    AlreadyIsGroupMember,
    AlreadyIsNotGroupMember,
    ConnectionNotFound,
    GroupAdminNotFound,
    GroupAlreadyExists,
    GroupNotFound,
    SyncmasterException,
    UsernameAlreadyExists,
    UserNotFound,
)

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    return exception_json_response(status_code=exc.status_code, detail=exc.detail)


async def syncmsater_exception_handler(request: Request, exc: SyncmasterException):
    if isinstance(exc, ActionNotAllowed):
        return exception_json_response(
            status_code=status.HTTP_403_FORBIDDEN, detail="You have no power here"
        )

    if isinstance(exc, GroupNotFound):
        return exception_json_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Group not found",
        )

    if isinstance(exc, GroupAdminNotFound):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Admin not found",
        )
    if isinstance(exc, GroupAlreadyExists):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Group name already taken",
        )

    if isinstance(exc, AlreadyIsNotGroupMember):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already is not group member",
        )

    if isinstance(exc, AlreadyIsGroupMember):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already is group member",
        )

    if isinstance(exc, UserNotFound):
        return exception_json_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if isinstance(exc, UsernameAlreadyExists):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already taken",
        )

    if isinstance(exc, ConnectionNotFound):
        return exception_json_response(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found",
        )

    if isinstance(exc, AclNotFound):
        return exception_json_response(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Rule was already deleted",
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
