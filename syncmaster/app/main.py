import uvicorn
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.config import get_settings


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

    return application


if __name__ == "__main__":
    app = get_application()
    uvicorn.run(app, host="0.0.0.0", port=8000)
