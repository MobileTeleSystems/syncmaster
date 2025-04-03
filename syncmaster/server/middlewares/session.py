# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from syncmaster.server.settings.server.session import SessionSettings


def apply_session_middleware(app: FastAPI, settings: SessionSettings) -> FastAPI:
    """Add SessionMiddleware middleware to the application."""

    app.add_middleware(
        SessionMiddleware,
        **settings.model_dump(),
    )
    return app
