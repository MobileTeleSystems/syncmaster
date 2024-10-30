# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import uuid

from asgi_correlation_id import CorrelationIdMiddleware
from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import async_engine_from_config
from starlette.middleware.cors import CORSMiddleware

from syncmaster.backend.api.router import api_router
from syncmaster.backend.handler import (
    http_exception_handler,
    syncmsater_exception_handler,
    unknown_exception_handler,
    validation_exception_handler,
)
from syncmaster.backend.services.unit_of_work import UnitOfWork
from syncmaster.db.factory import create_session_factory, get_uow
from syncmaster.exceptions import SyncmasterError
from syncmaster.settings import Settings


def application_factory(settings: Settings) -> FastAPI:
    application = FastAPI(
        title=settings.PROJECT_NAME,
        debug=settings.server.debug,
    )
    application.state.settings = settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.add_middleware(
        CorrelationIdMiddleware,
        header_name="X-Correlation-ID",
        generator=lambda: str(uuid.uuid4()),
    )

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

    return application


def get_application() -> FastAPI:
    return application_factory(settings=Settings())
