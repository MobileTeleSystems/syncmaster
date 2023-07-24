from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, create_async_engine

from app.config import Settings
from app.db.models import Group, User


class MockUser:
    def __init__(self, user: User, auth_token: str) -> None:
        self.user = user
        self.token = auth_token

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.user, attr)


class MockGroup:
    def __init__(self, group: Group, admin: MockUser, members: list[MockUser]):
        self.group = group
        self.admin = admin
        self.members = members

    def __getattr__(self, attr: str) -> Any:
        return getattr(self.group, attr)


async def database_exists(connection: AsyncConnection, db_name: str) -> bool:
    query = f"SELECT 1 from pg_database where datname='{db_name}'"
    if (await connection.execute(text(query))).scalar():
        return True
    return False


async def create_database(connection: AsyncConnection, db_name: str) -> None:
    await connection.execute(text("commit"))
    query = "CREATE DATABASE {} ENCODING {} TEMPLATE {}".format(
        db_name, "utf8", "template1"
    )
    await connection.execute(text(query))


async def drop_database(connection: AsyncConnection, db_name: str) -> None:
    await connection.execute(text("commit"))
    query = f"DROP DATABASE {db_name}"
    await connection.execute(text(query))


async def prepare_new_database(settings: Settings) -> None:
    """Using default postgres db for creating new test db"""
    connection_url = settings.build_db_connection_uri(database="postgres")

    engine = create_async_engine(connection_url, echo=True)
    async with engine.begin() as conn:
        if await database_exists(conn, settings.POSTGRES_DB):
            await drop_database(conn, settings.POSTGRES_DB)
        await create_database(conn, settings.POSTGRES_DB)
    await engine.dispose()
