# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import BaseModel, Field

from syncmaster.settings import (
    DEFAULT_LOGGING_SETTINGS,
    BaseSettings,
    CredentialsEncryptionSettings,
    DatabaseSettings,
    LoggingSettings,
    RabbitMQSettings,
)


class SchedulerSettings(BaseModel):
    """Scheduler settings.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        scheduler:
            transfer_fetching_timeout_seconds: 200
            misfire_grace_time_seconds: 300
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

    The settings can be passed in several ways:

    1. By storing settings in a configuration file ``config.yml`` (preferred).
    2. By setting environment variables matching specific keys (``SYNCMASTER__DATABASE__URL`` == ``database.url``).
    3. By explicitly passing a settings object as an argument of application factory function.

    More details can be found in
    `Pydantic documentation <https://docs.pydantic.dev/latest/concepts/pydantic_settings/>`_.

    Examples
    --------

    .. code-block:: yaml
        :caption: config.yml

        database:
            url: postgresql+asyncpg://postgres:postgres@localhost:5432/syncmaster

        broker:
            url: amqp://user:password@localhost:5672/

        logging: {}
        encryption: {}
        scheduler: {}
    """

    database: DatabaseSettings = Field(default_factory=DatabaseSettings, description="Database settings")
    broker: RabbitMQSettings = Field(default_factory=RabbitMQSettings, description="Broker settings")
    logging: LoggingSettings = Field(default=DEFAULT_LOGGING_SETTINGS, description="Logging settings")
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings, description="Scheduler-specific settings")
    encryption: CredentialsEncryptionSettings = Field(
        default_factory=CredentialsEncryptionSettings,
        description="Settings for encrypting credential data",
    )
