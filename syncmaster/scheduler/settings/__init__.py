# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import Field
from pydantic_settings import BaseSettings

from syncmaster.settings import (
    CredentialsEncryptionSettings,
    DatabaseSettings,
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
    """Scheduler application settings."""

    database: DatabaseSettings = Field(description="Database settings")
    broker: RabbitMQSettings = Field(description="Broker settings")
    scheduler: SchedulerSettings = Field(default_factory=SchedulerSettings, description="Scheduler-specific settings")
    encryption: CredentialsEncryptionSettings = Field(
        default_factory=CredentialsEncryptionSettings,
        description="Settings for encrypting credential data",
    )

    class Config:
        env_prefix = "SYNCMASTER__"
        env_nested_delimiter = "__"
