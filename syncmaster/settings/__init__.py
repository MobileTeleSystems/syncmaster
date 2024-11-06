# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum

from pydantic import Field
from pydantic.types import ImportString
from pydantic_settings import BaseSettings

from syncmaster.settings.auth import AuthSettings
from syncmaster.settings.broker import RabbitMQSettings
from syncmaster.settings.database import DatabaseSettings
from syncmaster.settings.server import ServerSettings
from syncmaster.settings.worker import WorkerSettings


class EnvTypes(StrEnum):
    LOCAL = "LOCAL"


# TODO: split settings into syncmaster/server/settings and syncmaster/worker/settings
class Settings(BaseSettings):
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

    CREATE_SPARK_SESSION_FUNCTION: ImportString = "syncmaster.worker.spark.get_worker_spark_session"

    database: DatabaseSettings = Field(description=":ref:`Database settings <backend-configuration-database>`")
    broker: RabbitMQSettings = Field(description=":ref:`Broker settings <backend-configuration-broker>`")
    server: ServerSettings = Field(
        default_factory=ServerSettings,
        description="Server settings <backend-configuration",
    )
    auth: AuthSettings = Field(
        default_factory=AuthSettings,
        description="Auth settings",
    )
    worker: WorkerSettings = Field(
        default_factory=WorkerSettings,
        description="Celery worker settings",
    )

    class Config:
        env_prefix = "SYNCMASTER__"
        env_nested_delimiter = "__"
