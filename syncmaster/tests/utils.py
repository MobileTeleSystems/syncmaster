from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.db.models import User


class MockUser:
    def __init__(self, user: User, auth_token: str):
        self.user = user
        self.token = auth_token

    def __getattr__(self, attr: str):
        return getattr(self.user, attr)


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
