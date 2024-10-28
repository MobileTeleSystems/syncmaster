# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

import textwrap

from pydantic import BaseModel, Field

from syncmaster.settings.server.log import LoggingSettings


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
            :ref:`Enable debug output in responses <backend-configuration-debug>`.
            Do not use this on production!
            """,
        ),
    )
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description=":ref:`Logging settings <backend-configuration-logging>`",
    )
