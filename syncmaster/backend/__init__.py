# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from starlette.middleware.cors import CORSMiddleware

from syncmaster.backend.api.deps import (
    DatabaseEngineMarker,
    DatabaseSessionMarker,
    SettingsMarker,
    UnitOfWorkMarker,
)
from syncmaster.backend.api.router import api_router
from syncmaster.backend.handler import (
    http_exception_handler,
    syncmsater_exception_handler,
    unknown_exception_handler,
    validation_exception_handler,
)
from syncmaster.config import Settings
from syncmaster.db.factory import create_engine, create_session_factory, get_uow
from syncmaster.exceptions import SyncmasterError


def application_factory(settings: Settings) -> FastAPI:
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
    application.exception_handler(RequestValidationError)(validation_exception_handler)
    application.exception_handler(ValidationError)(validation_exception_handler)
    application.exception_handler(SyncmasterError)(syncmsater_exception_handler)
    application.exception_handler(HTTPException)(http_exception_handler)
    application.exception_handler(Exception)(unknown_exception_handler)

    engine = create_engine(connection_uri=settings.build_db_connection_uri())
    session_factory = create_session_factory(engine=engine)

    application.dependency_overrides.update(
        {
            SettingsMarker: lambda: settings,
            DatabaseEngineMarker: lambda: engine,
            DatabaseSessionMarker: lambda: session_factory,
            UnitOfWorkMarker: get_uow(session_factory, settings),
        },
    )

    return application


def get_application() -> FastAPI:
    return application_factory(settings=Settings())
