# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic.types import ImportString

from syncmaster.settings import SyncmasterSettings


class WorkerSettings(SyncmasterSettings):
    """Celery worker settings.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__WORKER__LOGGING__PRESET=colored
    """

    CORRELATION_CELERY_HEADER_ID: str = "CORRELATION_CELERY_HEADER_ID"
    LOG_URL_TEMPLATE: str = ""

    CREATE_SPARK_SESSION_FUNCTION: ImportString = "syncmaster.worker.spark.get_worker_spark_session"


worker_settings = WorkerSettings()
