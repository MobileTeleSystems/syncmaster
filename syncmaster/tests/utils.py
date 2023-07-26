from typing import Any

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy import Connection, MetaData, pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    async_engine_from_config,
    create_async_engine,
)

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


def do_run_migrations(
    connection: Connection, target_metadata: MetaData, context: EnvironmentContext
) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(
    config: Config, target_metadata: MetaData, revision: str
) -> None:
    script = ScriptDirectory.from_config(config)

    def upgrade(rev, context):
        return script._upgrade_revs(revision, rev)

    with EnvironmentContext(
        config,
        script=script,
        fn=upgrade,
        as_sql=False,
        starting_rev=None,
        destination_rev=revision,
    ) as context:
        connectable = async_engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        async with connectable.connect() as connection:
            await connection.run_sync(
                do_run_migrations, target_metadata=target_metadata, context=context
            )

        await connectable.dispose()


def get_diff_db_metadata(connection: Connection, metadata: MetaData):
    migration_ctx = MigrationContext.configure(connection)
    return compare_metadata(context=migration_ctx, metadata=metadata)
