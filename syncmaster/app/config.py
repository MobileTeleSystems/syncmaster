from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    TEST: bool = False
    DEBUG: bool = False

    PROJECT_NAME: str = "SyncMaster"

    SECRET_KEY: str = "secret"
    SECURITY_ALGORITHM: str = "HS256"

    POSTGRES_HOST: str
    POSTGRES_PORT: int
    POSTGRES_DB: str
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    @property
    def DATABASE_URI(self) -> str:
        return "postgresql+asyncpg://{}:{}@{}:{}/{}".format(
            self.POSTGRES_USER,
            self.POSTGRES_PASSWORD,
            self.POSTGRES_HOST,
            self.POSTGRES_PORT,
            self.POSTGRES_DB,
        )

    TOKEN_EXPIRED_TIME: int = 60 * 60 * 10  # 10 hours


@lru_cache
def get_settings():
    return Settings()
