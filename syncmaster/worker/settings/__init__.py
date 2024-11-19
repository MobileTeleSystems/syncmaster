# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import Field
from pydantic.types import ImportString

from syncmaster.settings import SyncmasterSettings


class WorkerSettings(SyncmasterSettings):
    """Celery worker settings.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__WORKER__LOG_URL_TEMPLATE="https://grafana.example.com?correlation_id={{ correlation_id }}&run_id={{ run.id }}"
    """

    LOG_URL_TEMPLATE: str = Field(
        "",
        description="URL template for logging",
        alias="SYNCMASTER__WORKER__LOG_URL_TEMPLATE",
    )
    CORRELATION_CELERY_HEADER_ID: str = Field(
        "CORRELATION_CELERY_HEADER_ID",
        description="Header ID for correlation in Celery",
        alias="SYNCMASTER__WORKER__CORRELATION_CELERY_HEADER_ID",
    )
    CREATE_SPARK_SESSION_FUNCTION: ImportString = Field(
        "syncmaster.worker.spark.get_worker_spark_session",
        description="Function to create Spark session for worker",
        alias="SYNCMASTER__WORKER__CREATE_SPARK_SESSION_FUNCTION",
    )
