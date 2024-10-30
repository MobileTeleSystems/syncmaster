# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum

from pydantic import Field, model_validator
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

    PROJECT_NAME: str = "SyncMaster"

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


class TestSettings(BaseSettings):
    TEST_POSTGRES_HOST_FOR_CONFTEST: str
    TEST_POSTGRES_PORT_FOR_CONFTEST: int
    TEST_POSTGRES_HOST_FOR_WORKER: str
    TEST_POSTGRES_PORT_FOR_WORKER: int
    TEST_POSTGRES_DB: str
    TEST_POSTGRES_USER: str
    TEST_POSTGRES_PASSWORD: str

    TEST_ORACLE_HOST_FOR_CONFTEST: str
    TEST_ORACLE_PORT_FOR_CONFTEST: int
    TEST_ORACLE_HOST_FOR_WORKER: str
    TEST_ORACLE_PORT_FOR_WORKER: int
    TEST_ORACLE_USER: str
    TEST_ORACLE_PASSWORD: str
    TEST_ORACLE_SID: str | None = None
    TEST_ORACLE_SERVICE_NAME: str | None = None

    TEST_HIVE_CLUSTER: str
    TEST_HIVE_USER: str
    TEST_HIVE_PASSWORD: str

    TEST_HDFS_HOST: str
    TEST_HDFS_WEBHDFS_PORT: int
    TEST_HDFS_IPC_PORT: int

    TEST_S3_HOST_FOR_CONFTEST: str
    TEST_S3_PORT_FOR_CONFTEST: int
    TEST_S3_HOST_FOR_WORKER: str
    TEST_S3_PORT_FOR_WORKER: int
    TEST_S3_BUCKET: str
    TEST_S3_ACCESS_KEY: str
    TEST_S3_SECRET_KEY: str
    TEST_S3_PROTOCOL: str = "http"
    TEST_S3_ADDITIONAL_PARAMS: dict = {}

    @model_validator(mode="before")
    def check_sid_and_service_name(cls, values):
        sid = values.get("TEST_ORACLE_SID")
        service_name = values.get("TEST_ORACLE_SERVICE_NAME")
        if (sid is None) == (service_name is None):
            raise ValueError("Connection must have one param: sid or service name")
        return values
