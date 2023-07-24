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

    def build_db_connection_uri(
        self,
        *,
        host: str | None = None,
        port: int | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None
    ) -> str:
        return "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
            user or self.POSTGRES_USER,
            password or self.POSTGRES_PASSWORD,
            host or self.POSTGRES_HOST,
            port or self.POSTGRES_PORT,
            database or self.POSTGRES_DB,
        )

    TOKEN_EXPIRED_TIME: int = 60 * 60 * 10  # 10 hours
