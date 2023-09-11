from pydantic import BaseSettings


class Settings(BaseSettings):
    TEST: bool = False
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
