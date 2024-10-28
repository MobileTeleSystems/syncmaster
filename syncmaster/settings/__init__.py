# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from enum import StrEnum

from pydantic import Field, model_validator
from pydantic.types import ImportString
from pydantic_settings import BaseSettings

from syncmaster.settings.server import ServerSettings


class EnvTypes(StrEnum):
    LOCAL = "LOCAL"


class Settings(BaseSettings):
    """Syncmaster backend settings.

    Backend can be configured in 2 ways:

    * By explicitly passing ``settings`` object as an argument to :obj:`application_factory <syncmaster.backend.main.application_factory>`
    * By setting up environment variables matching a specific key.


    More details can be found in `Pydantic documentation <https://docs.pydantic.dev/latest/concepts/pydantic_settings/>`_.

    Examples
    --------

    .. code-block:: bash

        # same as settings.server.debug = True
        SERVER_DEBUG=True
    """

    SERVER_DEBUG: bool = True

    PROJECT_NAME: str = "SyncMaster"

    SECRET_KEY: str = "secret"
    SECURITY_ALGORITHM: str = "HS256"
    CRYPTO_KEY: str = "UBgPTioFrtH2unlC4XFDiGf5sYfzbdSf_VgiUSaQc94="

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    LOGGING_SYSTEM: str = "elk"

    LOG_URL_TEMPLATE: str = ""
    CORRELATION_CELERY_HEADER_ID: str = "CORRELATION_CELERY_HEADER_ID"

    def build_db_connection_uri(
        self,
        *,
        driver: str | None = None,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ) -> str:
        return "postgresql+{}://{}:{}@{}:{}/{}".format(
            driver or "asyncpg",
            user or self.POSTGRES_USER,
            password or self.POSTGRES_PASSWORD,
            host or self.POSTGRES_HOST,
            port or self.POSTGRES_PORT,
            database or self.POSTGRES_DB,
        )

    def build_rabbit_connection_uri(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
    ) -> str:
        return "amqp://{}:{}@{}:{}//".format(
            user or self.RABBITMQ_USER,
            password or self.RABBITMQ_PASSWORD,
            host or self.RABBITMQ_HOST,
            port or self.RABBITMQ_PORT,
        )

    TOKEN_EXPIRED_TIME: int = 60 * 60 * 10  # 10 hours
    CREATE_SPARK_SESSION_FUNCTION: ImportString = "syncmaster.worker.spark.get_worker_spark_session"

    server: ServerSettings = Field(
        default_factory=ServerSettings,
        description=":ref:`Server settings <backend-configuration>`",
    )


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
