from functools import lru_cache

from pydantic import BaseSettings


class Settings(BaseSettings):
    TEST: bool = False
    DEBUG: bool = False

    PROJECT_NAME: str = "SyncMaster"
    API_RPEFIX: str = "/v1"


@lru_cache
def get_settings(**kwargs):
    return Settings(**kwargs)
