from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseSettings, PyObject, root_validator

if TYPE_CHECKING:
    pass


class EnvTypes(StrEnum):
    LOCAL = "LOCAL"
    GITLAB = "GITLAB"


class Settings(BaseSettings):
    ENV: EnvTypes = EnvTypes.LOCAL
    DEBUG: bool = True

    PROJECT_NAME: str = "SyncMaster"

    SECRET_KEY: str = "secret"
    SECURITY_ALGORITHM: str = "HS256"
    AUTH_TOKEN_URL: str = "v1/auth/token"

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    RABBITMQ_HOST: str
    RABBITMQ_PORT: int
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    def build_db_connection_uri(
        self,
        *,
        driver: str | None = None,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None
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
        password: str | None = None
    ) -> str:
        return "amqp://{}:{}@{}:{}//".format(
            user or self.RABBITMQ_USER,
            password or self.RABBITMQ_PASSWORD,
            host or self.RABBITMQ_HOST,
            port or self.RABBITMQ_PORT,
        )

    TOKEN_EXPIRED_TIME: int = 60 * 60 * 10  # 10 hours

    IVYSETTINGS_PATH = Path(__file__).parent.parent / "config" / "ivysettings.xml"
    CREATE_SPARK_SESSION_FUNCTION: PyObject = "app.tasks.utils.get_worker_spark_session"  # type: ignore[assignment]


class TestSettings(BaseSettings):
    TEST_POSTGRES_HOST: str
    TEST_POSTGRES_PORT: int
    TEST_POSTGRES_DB: str
    TEST_POSTGRES_USER: str
    TEST_POSTGRES_PASSWORD: str

    TEST_ORACLE_HOST: str
    TEST_ORACLE_PORT: int
    TEST_ORACLE_USER: str
    TEST_ORACLE_PASSWORD: str
    TEST_ORACLE_SID: str | None = None
    TEST_ORACLE_SERVICE_NAME: str | None = None

    @root_validator
    def check_sid_and_service_name(cls, values):
        sid = values.get("TEST_ORACLE_SID")
        service_name = values.get("TEST_ORACLE_SERVICE_NAME")
        if (sid is None) == (service_name is None):
            raise ValueError("Connection must have one param: sid or service name")
        return values
