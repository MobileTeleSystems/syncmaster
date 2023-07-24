import logging

from fastapi import HTTPException, Request, status
from fastapi.responses import JSONResponse

from app.api.v1.schemas import StatusResponseSchema
from app.exceptions import SyncmasterException

logger = logging.getLogger(__name__)


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=StatusResponseSchema(
            ok=False,
            status_code=exc.status_code,
            message=exc.detail,
        ).dict(),
    )


async def syncmsater_exception_handler(request: Request, exc: SyncmasterException):
    logger.exception("Got unhandled error")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=StatusResponseSchema(
            ok=False,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Got unhandled exception. See logs",
        ).dict(),
    )
