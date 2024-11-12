# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_engine_from_config

from syncmaster.backend.api.router import api_router
from syncmaster.backend.handler import (
    http_exception_handler,
    syncmsater_exception_handler,
    unknown_exception_handler,
    validation_exception_handler,
)
from syncmaster.backend.middlewares import apply_middlewares
from syncmaster.backend.providers.auth import AuthProvider
from syncmaster.backend.services.unit_of_work import UnitOfWork
from syncmaster.backend.settings import BackendSettings as Settings
from syncmaster.db.factory import create_session_factory, get_uow
from syncmaster.exceptions import SyncmasterError


def application_factory(settings: Settings) -> FastAPI:
    application = FastAPI(
        title="Syncmaster",
        debug=settings.server.debug,
        # will be set up by middlewares
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )
    application.state.settings = settings
    application.include_router(api_router)
    application.exception_handler(RequestValidationError)(validation_exception_handler)
    application.exception_handler(ValidationError)(validation_exception_handler)
    application.exception_handler(SyncmasterError)(syncmsater_exception_handler)
    application.exception_handler(HTTPException)(http_exception_handler)
    application.exception_handler(Exception)(unknown_exception_handler)

    engine = async_engine_from_config(settings.database.dict(), prefix="")
    session_factory = create_session_factory(engine=engine)

    application.dependency_overrides.update(
        {
            Settings: lambda: settings,
            UnitOfWork: get_uow(session_factory, settings=settings),
        },
    )

    auth_class = settings.auth.provider
    auth_class.setup(application)

    apply_middlewares(application, settings)
    return application


def get_application() -> FastAPI:
    return application_factory(settings=Settings())
