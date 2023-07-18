import uvicorn
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings
from app.handler import http_exception_handler


def get_application() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.PROJECT_NAME,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)
    application.exception_handler(HTTPException)(http_exception_handler)

    return application


if __name__ == "__main__":
    app = get_application()
    uvicorn.run(app, host="0.0.0.0", port=8000)
