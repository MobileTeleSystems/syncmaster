# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from fastapi import FastAPI

from syncmaster.server.middlewares.cors import apply_cors_middleware
from syncmaster.server.middlewares.monitoring.metrics import (
    apply_monitoring_metrics_middleware,
)
from syncmaster.server.middlewares.openapi import apply_openapi_middleware
from syncmaster.server.middlewares.request_id import apply_request_id_middleware
from syncmaster.server.middlewares.session import apply_session_middleware
from syncmaster.server.middlewares.static_files import apply_static_files
from syncmaster.server.settings import ServerAppSettings as Settings
from syncmaster.settings.log import setup_logging


def apply_middlewares(
    application: FastAPI,
    settings: Settings,
) -> FastAPI:
    """Add middlewares to the application."""

    if settings.logging.setup:
        setup_logging(settings.logging.get_log_config_path())

    apply_cors_middleware(application, settings.server.cors)
    apply_monitoring_metrics_middleware(application, settings.server.monitoring)
    apply_request_id_middleware(application, settings.server.request_id)
    apply_openapi_middleware(application, settings.server.openapi)
    apply_static_files(application, settings.server.static_files)
    apply_session_middleware(application, settings.server.session)

    return application
