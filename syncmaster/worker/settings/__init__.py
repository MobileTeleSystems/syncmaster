# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
import importlib
import os

from pydantic import Field
from pydantic.types import ImportString
from pydantic_settings import BaseSettings

from syncmaster.settings import (
    CredentialsEncryptionSettings,
    DatabaseSettings,
    LoggingSettings,
    RabbitMQSettings,
)


class WorkerSettings(BaseSettings):
    """Celery worker settings.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__WORKER__LOG_URL_TEMPLATE="https://grafana.example.com?correlation_id={{ correlation_id }}&run_id={{ run.id }}"
    """

    LOG_URL_TEMPLATE: str = Field(
        "",
        description="URL template for logging",
    )
    CORRELATION_CELERY_HEADER_ID: str = Field(
        "CORRELATION_CELERY_HEADER_ID",
        description="Header ID for correlation in Celery",
    )
    CREATE_SPARK_SESSION_FUNCTION: ImportString = Field(
        "syncmaster.worker.spark.get_worker_spark_session",
        description="Function to create Spark session for worker",
    )


class WorkerAppSettings(BaseSettings):

    database: DatabaseSettings = Field(description="Database settings")
    broker: RabbitMQSettings = Field(description="Broker settings")
    logging: LoggingSettings = Field(default_factory=LoggingSettings, description="Logging settings")
    worker: WorkerSettings = Field(default_factory=WorkerSettings, description="Worker-specific settings")
    encryption: CredentialsEncryptionSettings = Field(
        default_factory=CredentialsEncryptionSettings,
        description="Settings for encrypting credential data",
    )

    class Config:
        env_prefix = "SYNCMASTER__"
        env_nested_delimiter = "__"


def get_worker_settings() -> WorkerAppSettings:
    # TODO: add to worker documentation
    worker_settings_path = os.environ.get("WORKER_SETTINGS", None)

    if worker_settings_path:
        module_name, class_name = worker_settings_path.rsplit(".", 1)
        module = importlib.import_module(module_name)
        settings_class = getattr(module, class_name)
    else:
        settings_class = WorkerAppSettings
    return settings_class()
