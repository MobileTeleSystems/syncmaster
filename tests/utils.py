import asyncio
import logging
from datetime import datetime
from typing import Any

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from httpx import AsyncClient
from sqlalchemy import Connection as AlchConnection
from sqlalchemy import MetaData, pool, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    async_engine_from_config,
    create_async_engine,
)

from syncmaster.config import Settings
from syncmaster.db.models import Status

logger = logging.getLogger(__name__)


async def prepare_new_database(settings: Settings) -> None:
    """Using default postgres db for creating new test db"""
    connection_url = settings.build_db_connection_uri(database="postgres")

    engine = create_async_engine(connection_url, echo=True)
    async with engine.begin() as conn:
        if not await database_exists(conn, settings.POSTGRES_DB):
            await create_database(conn, settings.POSTGRES_DB)
    await engine.dispose()


def do_run_migrations(connection: AlchConnection, target_metadata: MetaData, context: EnvironmentContext) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations(config: Config, target_metadata: MetaData, revision: str, action="up") -> None:
    script = ScriptDirectory.from_config(config)

    def upgrade(rev, context):
        return script._upgrade_revs(revision, rev)

    def downgrade(rev, context):
        return script._downgrade_revs(revision, rev)

    with EnvironmentContext(
        config,
        script=script,
        fn=upgrade if action == "up" else downgrade,
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
            await connection.run_sync(do_run_migrations, target_metadata=target_metadata, context=context)

        await connectable.dispose()


def get_diff_db_metadata(connection: AlchConnection, metadata: MetaData):
    migration_ctx = MigrationContext.configure(connection)
    return compare_metadata(context=migration_ctx, metadata=metadata)


async def database_exists(connection: AsyncConnection, db_name: str) -> bool:
    query = f"SELECT 1 from pg_database where datname='{db_name}'"
    if await connection.scalar(text(query)):
        return True
    return False


async def create_database(connection: AsyncConnection, db_name: str) -> None:
    await connection.execute(text("commit"))
    query = "CREATE DATABASE {} ENCODING {} TEMPLATE {}".format(db_name, "utf8", "template1")
    await connection.execute(text(query))


async def drop_database(connection: AsyncConnection, db_name: str) -> None:
    await connection.execute(text("commit"))
    query = f"DROP DATABASE {db_name}"
    await connection.execute(text(query))


async def get_run_on_end(
    client: AsyncClient,
    run_id: int,
    token: str,
    timeout: int = 120,
) -> dict[str, Any]:
    end_time = datetime.now().timestamp() + timeout
    while True:
        logger.info("Waiting for end of run")
        result = await client.get(
            f"v1/runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if result.status_code != 200:
            raise Exception("Run not found")

        data = result.json()
        if data["status"] in [Status.FINISHED, Status.FAILED]:
            return data

        if datetime.now().timestamp() > end_time:
            raise TimeoutError()

        await asyncio.sleep(1)
