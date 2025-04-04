# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

import textwrap

from pydantic import BaseModel, Field

from syncmaster.server.settings.server.cors import CORSSettings
from syncmaster.server.settings.server.monitoring import MonitoringSettings
from syncmaster.server.settings.server.openapi import OpenAPISettings
from syncmaster.server.settings.server.request_id import RequestIDSettings
from syncmaster.server.settings.server.session import SessionSettings
from syncmaster.server.settings.server.static_files import StaticFilesSettings


class ServerSettings(BaseModel):
    """Server server settings.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__SERVER__DEBUG=True
        SYNCMASTER__SERVER__REQUEST_ID__ENABLED=True
        SYNCMASTER__SERVER__MONITORING__ENABLED=True
    """

    debug: bool = Field(
        default=False,
        description=textwrap.dedent(
            """
            :ref:`Enable debug output in responses <server-configuration-debug>`.
            Do not use this on production!
            """,
        ),
    )
    request_id: RequestIDSettings = Field(
        default_factory=RequestIDSettings,
    )
    session: SessionSettings = Field(
        default_factory=SessionSettings,  # type: ignore[arg-type]
        description=":ref:`Session settings <server-configuration-session>`",
    )
    cors: CORSSettings = Field(
        default_factory=CORSSettings,
        description=":ref:`CORS settings <server-configuration-cors>`",
    )
    monitoring: MonitoringSettings = Field(
        default_factory=MonitoringSettings,
        description=":ref:`Monitoring settings <server-configuration-monitoring>`",
    )
    openapi: OpenAPISettings = Field(
        default_factory=OpenAPISettings,
        description=":ref:`OpenAPI.json settings <server-configuration-openapi>`",
    )
    static_files: StaticFilesSettings = Field(
        default_factory=StaticFilesSettings,
        description=":ref:`Static files settings <server-configuration-static-files>`",
    )
