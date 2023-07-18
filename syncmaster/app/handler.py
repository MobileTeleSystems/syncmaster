from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from app.api.v1.schemas import StatusResponseSchema


async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=StatusResponseSchema(
            ok=False,
            status_code=exc.status_code,
            message=exc.detail,
        ).dict(),
    )
