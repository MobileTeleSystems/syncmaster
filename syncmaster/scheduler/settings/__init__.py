# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from syncmaster.settings import (
    CredentialsEncryptionSettings,
    DatabaseSettings,
    LoggingSettings,
    RabbitMQSettings,
)


class SchedulerSettings(BaseSettings):
    """Celery scheduler settings.

    Examples
    --------

    .. code-block:: bash

        SYNCMASTER__SCHEDULER__TRANSFER_FETCHING_TIMEOUT_SECONDS=200
    """

    TRANSFER_FETCHING_TIMEOUT_SECONDS: int = Field(
        180,
        description="Timeout for fetching transfers in seconds",
    )
    MISFIRE_GRACE_TIME_SECONDS: int = Field(
        300,
        description="Grace time for misfired jobs in seconds",
    )


class SchedulerAppSettings(BaseSettings):
    """
    Scheduler application settings.

    This class is used to configure various settings for the scheduler application.
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

        # Example of setting a TRANSFER_FETCHING_TIMEOUT_SECONDS via environment variable
        SYNCMASTER__SCHEDULER__TRANSFER_FETCHING_TIMEOUT_SECONDS=200

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
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings, description="Scheduler-specific settings")
    encryption: CredentialsEncryptionSettings = Field(
        default_factory=CredentialsEncryptionSettings,
        description="Settings for encrypting credential data",
    )

    model_config = SettingsConfigDict(env_prefix="SYNCMASTER__", env_nested_delimiter="__")
