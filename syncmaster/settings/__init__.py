# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum

from pydantic import Field
from pydantic_settings import BaseSettings

from syncmaster.settings.broker import RabbitMQSettings
from syncmaster.settings.database import DatabaseSettings
from syncmaster.settings.log import LoggingSettings


class EnvTypes(StrEnum):
    LOCAL = "LOCAL"


class SyncmasterSettings(BaseSettings):
    """Syncmaster backend settings.

    Backend can be configured in 2 ways:

    * By explicitly passing ``settings`` object as an argument to :obj:`application_factory <syncmaster.backend.main.application_factory>`
    * By setting up environment variables matching a specific key.

        All environment variable names are written in uppercase and should be prefixed with ``SYNCMASTER__``.
        Nested items are delimited with ``__``.


    More details can be found in
    `Pydantic documentation <https://docs.pydantic.dev/latest/concepts/pydantic_settings/>`_.

    Examples
    --------

    .. code-block:: bash

        # same as settings.database.url = "postgresql+asyncpg://postgres:postgres@localhost:5432/syncmaster"
        SYNCMASTER__DATABASE__URL=postgresql+asyncpg://postgres:postgres@localhost:5432/syncmaster

        # same as settings.server.debug = True
        SYNCMASTER__SERVER__DEBUG=True
    """

    crypto_key: str

    # TODO: move settings to corresponding classes (scheduler also)
    TZ: str = "UTC"
    SCHEDULER_TRANSFER_FETCHING_TIMEOUT: int = 180  # seconds
    SCHEDULER_MISFIRE_GRACE_TIME: int = 300  # seconds

    database: DatabaseSettings = Field(description=":ref:`Database settings <backend-configuration-database>`")
    broker: RabbitMQSettings = Field(description=":ref:`Broker settings <backend-configuration-broker>`")
    logging: LoggingSettings = Field(
        default_factory=LoggingSettings,
        description=":ref:`Logging settings <backend-configuration-logging>`",
    )

    class Config:
        env_prefix = "SYNCMASTER__"
        env_nested_delimiter = "__"
