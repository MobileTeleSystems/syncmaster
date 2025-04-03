# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import Field
from pydantic.types import ImportString
from pydantic_settings import BaseSettings, SettingsConfigDict

from syncmaster.settings import (
    CredentialsEncryptionSettings,
    DatabaseSettings,
    LoggingSettings,
    RabbitMQSettings,
)
from syncmaster.worker.settings.hwm_store import HWMStoreSettings


class WorkerSettings(BaseSettings):
    """Celery worker settings.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__WORKER__CREATE_SPARK_SESSION_FUNCTION=custom_syncmaster.spark.get_worker_spark_session
        SYNCMASTER__WORKER__LOG_URL_TEMPLATE=https://logs.location.example.com/syncmaster-worker?correlation_id={{ correlation_id }}&run_id={{ run.id }}
    """

    CREATE_SPARK_SESSION_FUNCTION: ImportString = Field(
        "syncmaster.worker.spark.get_worker_spark_session",
        description="Function to create Spark session for worker",
    )
    log_url_template: str = Field(
        "",
        description=":ref:`URL template to access worker logs <worker-log-url>`",
    )


class WorkerAppSettings(BaseSettings):
    """
    Worker application settings.

    This class is used to configure various settings for the worker application.
    The settings can be defined in two ways:

    1. By explicitly passing a settings object as an argument.
    2. By setting environment variables matching specific keys.

    All environment variable names are written in uppercase and should be prefixed with ``SYNCMASTER__``.
    Nested items are delimited with ``__``.

    More details can be found in
    `Pydantic documentation <https://docs.pydantic.dev/latest/concepts/pydantic_settings/>`_.

    Examples
    --------

    .. code-block:: bash

        # Example of setting a database URL via environment variable
        SYNCMASTER__DATABASE__URL=postgresql+asyncpg://user:password@localhost:5432/dbname

        # Example of setting a broker URL via environment variable
        SYNCMASTER__BROKER__URL=amqp://user:password@localhost:5672/

    Refer to `Pydantic documentation <https://docs.pydantic.dev/latest/concepts/pydantic_settings/>`_
    for more details on configuration options and environment variable usage.
    """

    database: DatabaseSettings = Field(description="Database settings")
    broker: RabbitMQSettings = Field(description="Broker settings")
    logging: LoggingSettings = Field(default_factory=LoggingSettings, description="Logging settings")
    worker: WorkerSettings = Field(default_factory=WorkerSettings, description="Worker-specific settings")
    encryption: CredentialsEncryptionSettings = Field(
        default_factory=CredentialsEncryptionSettings,
        description="Settings for encrypting credential data",
    )
    hwm_store: HWMStoreSettings = Field(default_factory=HWMStoreSettings, description="HWM Store settings")

    model_config = SettingsConfigDict(env_prefix="SYNCMASTER__", env_nested_delimiter="__")
