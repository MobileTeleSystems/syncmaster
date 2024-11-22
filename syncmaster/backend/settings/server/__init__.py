# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

import textwrap

from pydantic import BaseModel, Field

from syncmaster.backend.settings.server.cors import CORSSettings
from syncmaster.backend.settings.server.monitoring import MonitoringSettings
from syncmaster.backend.settings.server.openapi import OpenAPISettings
from syncmaster.backend.settings.server.request_id import RequestIDSettings
from syncmaster.backend.settings.server.session import SessionSettings
from syncmaster.backend.settings.server.static_files import StaticFilesSettings


class ServerSettings(BaseModel):
    """Backend server settings.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__SERVER__DEBUG=True
        SYNCMASTER__SERVER__LOGGING__PRESET=colored
    """

    debug: bool = Field(
        default=False,
        description=textwrap.dedent(
            """
            Enable debug output in responses.
            Do not use this on production!
            """,
        ),
    )
    log_url_template: str = Field(
        "",
        description="URL template for logging",
    )
    request_id: RequestIDSettings = Field(
        default_factory=RequestIDSettings,
    )
    session: SessionSettings = Field(
        default_factory=SessionSettings,  # type: ignore[arg-type]
        description=":ref:`Session settings <backend-configuration-server-session>`",
    )
    cors: CORSSettings = Field(
        default_factory=CORSSettings,
        description=":ref:`CORS settings <backend-configuration-server-cors>`",
    )
    monitoring: MonitoringSettings = Field(
        default_factory=MonitoringSettings,
        description=":ref:`Monitoring settings <backend-configuration-server-monitoring>`",
    )
    openapi: OpenAPISettings = Field(
        default_factory=OpenAPISettings,
        description=":ref:`OpenAPI.json settings <backend-configuration-server-openapi>`",
    )
    static_files: StaticFilesSettings = Field(
        default_factory=StaticFilesSettings,
        description=":ref:`Static files settings <backend-configuration-server-static-files>`",
    )
