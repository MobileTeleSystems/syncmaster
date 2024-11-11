# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

import textwrap

from pydantic import BaseModel, Field

from syncmaster.settings.log import LoggingSettings
from syncmaster.settings.server.cors import CORSSettings
from syncmaster.settings.server.monitoring import MonitoringSettings
from syncmaster.settings.server.openapi import OpenAPISettings
from syncmaster.settings.server.request_id import RequestIDSettings
from syncmaster.settings.server.static_files import StaticFilesSettings


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
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description=":ref:`Logging settings <backend-configuration-logging>`",
    )
    request_id: RequestIDSettings = Field(
        default_factory=RequestIDSettings,
    )
    cors: CORSSettings = Field(
        default_factory=CORSSettings,
        description=":ref:`CORS settings <backend-configuration-cors>`",
    )
    monitoring: MonitoringSettings = Field(
        default_factory=MonitoringSettings,
        description=":ref:`Monitoring settings <backend-configuration-monitoring>`",
    )
    openapi: OpenAPISettings = Field(
        default_factory=OpenAPISettings,
        description=":ref:`OpenAPI.json settings <backend-configuration-openapi>`",
    )
    static_files: StaticFilesSettings = Field(
        default_factory=StaticFilesSettings,
        description=":ref:`Static files settings <configuration-server-static-files>`",
    )
