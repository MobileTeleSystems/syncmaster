import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from httpx import AsyncClient
from onetl.connection import FileConnection
from onetl.file import FileDownloader, FileUploader
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, date_trunc
from sqlalchemy import Connection as AlchConnection
from sqlalchemy import MetaData, pool, text
from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    async_engine_from_config,
    create_async_engine,
)

from syncmaster.db.models import Status
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.mocks import MockUser

logger = logging.getLogger(__name__)


async def prepare_new_database(settings: Settings) -> None:
    """Using default postgres db for creating new test db"""
    connection_url = settings.database.url
    engine = create_async_engine(connection_url, echo=True)

    async with engine.begin() as conn:
        if not await database_exists(conn, "postgres"):
            await create_database(conn, "postgres")
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


def verify_transfer_auth_data(run_data: dict[str, Any]) -> None:
    source_auth_data = run_data["transfer_dump"]["source_connection"]["auth_data"]
    target_auth_data = run_data["transfer_dump"]["target_connection"]["auth_data"]

    assert source_auth_data["user"]
    assert "password" not in source_auth_data
    assert target_auth_data["user"]
    assert "password" not in target_auth_data


async def run_transfer_and_verify(client: AsyncClient, user: MockUser, transfer_id: int) -> dict[str, Any]:
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": transfer_id},
    )
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=user.token,
    )
    assert run_data["status"] == Status.FINISHED.value
    verify_transfer_auth_data(run_data)

    return run_data


def prepare_dataframes_for_comparison(
    df: DataFrame,
    init_df: DataFrame,
    file_format: str,
) -> tuple[DataFrame, DataFrame]:
    # as Excel does not support datetime values with precision greater than milliseconds
    if file_format == "excel":
        df = df.withColumn("REGISTERED_AT", date_trunc("second", col("REGISTERED_AT")))
        init_df = init_df.withColumn("REGISTERED_AT", date_trunc("second", col("REGISTERED_AT")))

    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    return df, init_df


def add_increment_to_files_and_upload(file_connection: FileConnection, remote_path: str, tmp_path: Path) -> None:
    downloader = FileDownloader(
        connection=file_connection,
        source_path=remote_path,
        local_path=tmp_path,
    )
    downloader.run()

    for file in tmp_path.iterdir():
        if file.is_file():
            # do not use file.suffix field, as extensions may include compression
            stem, suffix = file.name.split(".", 1)
            new_name = f"{stem}_increment.{suffix}"
            new_path = file.with_name(new_name)
            file.rename(new_path)

    uploader = FileUploader(
        connection=file_connection,
        local_path=tmp_path,
        target_path=remote_path,
    )
    uploader.run()
