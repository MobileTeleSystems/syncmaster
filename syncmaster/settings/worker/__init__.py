# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field

from syncmaster.settings.log import LoggingSettings


class WorkerSettings(BaseModel):
    """Celery worker settings.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__WORKER__LOGGING__PRESET=colored
    """

    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description=":ref:`Logging settings <configuration-logging>`",
    )
    CORRELATION_CELERY_HEADER_ID: str = "CORRELATION_CELERY_HEADER_ID"
    LOG_URL_TEMPLATE: str = ""
