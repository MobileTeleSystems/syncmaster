# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import secrets

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware


def apply_session_middleware(app: FastAPI) -> FastAPI:
    """Add SessionMiddleware middleware to the application."""
    secret_key = secrets.token_urlsafe(32)
    app.add_middleware(SessionMiddleware, secret_key=secret_key)
    return app
