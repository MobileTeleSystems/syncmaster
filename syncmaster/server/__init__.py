# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from celery import Celery
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_engine_from_config

from syncmaster import _raw_version as syncmaster_version
from syncmaster.db.factory import create_session_factory, get_uow
from syncmaster.exceptions import SyncmasterError
from syncmaster.server.api.router import api_router
from syncmaster.server.handler import (
    http_exception_handler,
    syncmsater_exception_handler,
    unknown_exception_handler,
    validation_exception_handler,
)
from syncmaster.server.middlewares import apply_middlewares
from syncmaster.server.providers.auth import AuthProvider
from syncmaster.server.services.unit_of_work import UnitOfWork
from syncmaster.server.settings import ServerAppSettings as Settings

__all__ = ["get_application", "application_factory"]


def celery_factory(settings: Settings) -> Celery:
    app = Celery(
        __name__,
        broker=settings.broker.url,
        backend="db+" + settings.database.sync_url,  # noqa: WPS336
    )
    return app


def application_factory(settings: Settings) -> FastAPI:
    application = FastAPI(
        title="SyncMaster",
        version=syncmaster_version,
        debug=settings.server.debug,
        # will be set up by middlewares
        openapi_url=None,
        docs_url=None,
        redoc_url=None,
    )
    application.state.settings = settings
    application.state.celery = celery_factory(settings)
    application.include_router(api_router)
    application.exception_handler(RequestValidationError)(validation_exception_handler)
    application.exception_handler(ValidationError)(validation_exception_handler)
    application.exception_handler(SyncmasterError)(syncmsater_exception_handler)
    application.exception_handler(HTTPException)(http_exception_handler)
    application.exception_handler(Exception)(unknown_exception_handler)

    engine = async_engine_from_config(settings.database.model_dump(), prefix="")
    session_factory = create_session_factory(engine=engine)

    application.dependency_overrides.update(
        {
            Settings: lambda: settings,
            UnitOfWork: get_uow(session_factory, settings=settings),
            Celery: lambda: application.state.celery,
        },
    )

    auth_class: type[AuthProvider] = settings.auth.provider  # type: ignore[assignment]
    auth_class.setup(application)

    apply_middlewares(application, settings)
    return application


def get_application() -> FastAPI:
    return application_factory(settings=Settings())
