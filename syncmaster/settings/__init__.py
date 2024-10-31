# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum

from pydantic import Field
from pydantic.types import ImportString
from pydantic_settings import BaseSettings

from syncmaster.settings.broker import RabbitMQSettings
from syncmaster.settings.database import DatabaseSettings
from syncmaster.settings.server import ServerSettings


class EnvTypes(StrEnum):
    LOCAL = "LOCAL"


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

    # TODO: move settings to corresponding classes
    SECRET_KEY: str = "secret"
    SECURITY_ALGORITHM: str = "HS256"
    CRYPTO_KEY: str = "UBgPTioFrtH2unlC4XFDiGf5sYfzbdSf_VgiUSaQc94="

    CORRELATION_CELERY_HEADER_ID: str = "CORRELATION_CELERY_HEADER_ID"

    TOKEN_EXPIRED_TIME: int = 60 * 60 * 10  # 10 hours
    CREATE_SPARK_SESSION_FUNCTION: ImportString = "syncmaster.worker.spark.get_worker_spark_session"

    database: DatabaseSettings = Field(description=":ref:`Database settings <backend-configuration-database>`")
    broker: RabbitMQSettings = Field(description=":ref:`Broker settings <backend-configuration-broker>`")
    server: ServerSettings = Field(
        default_factory=ServerSettings,
        description=":ref:`Server settings <backend-configuration>`",
    )

    class Config:
        env_prefix = "SYNCMASTER__"
        env_nested_delimiter = "__"
