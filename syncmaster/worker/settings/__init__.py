# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
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

        SYNCMASTER__WORKER__CREATE_SPARK_SESSION_FUNCTION=custom_syncmaster.spark.get_worker_spark_session
    """

    CREATE_SPARK_SESSION_FUNCTION: ImportString = Field(
        "syncmaster.worker.spark.get_worker_spark_session",
        description="Function to create Spark session for worker",
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

    class Config:
        env_prefix = "SYNCMASTER__"
        env_nested_delimiter = "__"
