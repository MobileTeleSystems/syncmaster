import uvicorn
from fastapi import FastAPI, HTTPException
from starlette.middleware.cors import CORSMiddleware

from app.api.deps import (
    AuthMarker,
    DatabaseEngineMarker,
    DatabaseSessionMarker,
    SettingsMarker,
    UnitOfWorkMarker,
)
from app.api.router import api_router
from app.config import Settings
from app.db.factory import create_engine, create_session_factory, get_uow
from app.exceptions import SyncmasterError
from app.handler import http_exception_handler, syncmsater_exception_handler
from app.services import get_auth_scheme


def get_application(settings: Settings) -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.DEBUG,
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
    application.exception_handler(SyncmasterError)(syncmsater_exception_handler)

    engine = create_engine(connection_uri=settings.build_db_connection_uri())
    session_factory = create_session_factory(engine=engine)

    auth_scheme = get_auth_scheme(settings)

    application.dependency_overrides.update(
        {
            SettingsMarker: lambda: settings,
            DatabaseEngineMarker: lambda: engine,
            DatabaseSessionMarker: lambda: session_factory,
            UnitOfWorkMarker: get_uow(session_factory, settings),
            AuthMarker: auth_scheme,
        }
    )

    return application


if __name__ == "__main__":
    settings = Settings()
    app = get_application(settings=settings)
    uvicorn.run(app, host="0.0.0.0", port=8000)
