# SPDX-FileCopyrightText: 2023-2025 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from fastapi import APIRouter, FastAPI
from starlette.responses import PlainTextResponse
from starlette_exporter import PrometheusMiddleware, handle_metrics

from syncmaster.server.settings.server.monitoring import MonitoringSettings
from syncmaster.server.utils.slug import slugify

DEFAULT_SKIP_PATHS = {
    "/monitoring/metrics",
    "/monitoring/ping",
    "/static",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/favicon.ico",
}

router = APIRouter(tags=["Monitoring"], prefix="/monitoring")


router.get(
    "/metrics",
    summary="Get server metrics",
    description="Return server metrics in Prometheus format, using Starlette Exporter",
    response_class=PlainTextResponse,
)(handle_metrics)


def apply_monitoring_metrics_middleware(app: FastAPI, settings: MonitoringSettings) -> FastAPI:
    """Add monitoring metrics middleware & endpoint to the application."""
    if not settings.enabled:
        return app

    skip_paths = DEFAULT_SKIP_PATHS | settings.skip_paths
    app.add_middleware(
        PrometheusMiddleware,
        app_name=slugify(app.title),
        skip_paths=skip_paths,
        **settings.model_dump(exclude={"enabled", "skip_paths"}),
    )
    app.include_router(router)
    return app
