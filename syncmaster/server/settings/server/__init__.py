# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

import textwrap

from pydantic import BaseModel, Field

from syncmaster.server.settings.server.cors import CORSSettings
from syncmaster.server.settings.server.monitoring import MonitoringSettings
from syncmaster.server.settings.server.openapi import OpenAPISettings
from syncmaster.server.settings.server.request_id import RequestIDSettings
from syncmaster.server.settings.server.static_files import StaticFilesSettings


class ServerSettings(BaseModel):
    """Server server settings.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        server:
            debug: true
            request_id:
                enabled: true
            cors:
                enabled: true
            monitoring:
                enabled: true
            openapi:
                enabled: true
            static_files:
                enabled: true
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
