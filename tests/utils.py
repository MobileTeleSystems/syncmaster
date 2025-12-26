import asyncio
import logging
from datetime import UTC, datetime
from pathlib import Path, PurePath, PurePosixPath
from typing import Any
from collections.abc import Sequence

from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.runtime.environment import EnvironmentContext
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from httpx import AsyncClient
from onetl.connection import FileConnection
from onetl.file import FileDownloader, FileUploader
from pyspark.sql import DataFrame
from pyspark.sql.functions import (
    col,
    date_format,
    date_trunc,
    from_unixtime,
    to_timestamp,
)
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
    return await connection.scalar(text(query))


async def create_database(connection: AsyncConnection, db_name: str) -> None:
    await connection.execute(text("commit"))
    query_template = "CREATE DATABASE {db} ENCODING {encoding} TEMPLATE {template}"
    query = query_template.format(db=db_name, encoding="utf8", template="template1")
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
    end_time = datetime.now(tz=UTC).timestamp() + timeout
    while True:
        logger.info("Waiting for end of run")
        response = await client.get(
            f"v1/runs/{run_id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        if response.status_code != 200:
            raise Exception("Run not found")

        data = response.json()
        if data["status"] in [Status.FINISHED, Status.FAILED]:
            return data

        if datetime.now(tz=UTC).timestamp() > end_time:
            raise TimeoutError

        await asyncio.sleep(1)


def verify_transfer_auth_data(run_data: dict[str, Any], source_auth: str, target_auth: str) -> None:
    for auth_type, auth_data in [
        (source_auth, run_data["transfer_dump"]["source_connection"]["auth_data"]),
        (target_auth, run_data["transfer_dump"]["target_connection"]["auth_data"]),
    ]:
        if auth_type == "s3":
            assert auth_data["access_key"]
            assert "secret_key" not in auth_data
        elif auth_type == "iceberg_rest_bearer":
            assert "rest_catalog_token" not in auth_data
        elif auth_type == "iceberg_rest_bearer_s3_basic":
            assert auth_data["s3_access_key"]
            assert "s3_secret_key" not in auth_data
            assert "rest_catalog_token" not in auth_data
        elif auth_type == "iceberg_rest_oauth2_client_credentials":
            assert auth_data["rest_catalog_oauth2_client_id"]
            assert "rest_catalog_oauth2_client_secret" not in auth_data
        elif auth_type == "iceberg_rest_oauth2_client_credentials_s3_basic":
            assert auth_data["s3_access_key"]
            assert auth_data["rest_catalog_oauth2_client_id"]
            assert "s3_secret_key" not in auth_data
            assert "rest_catalog_oauth2_client_secret" not in auth_data
        else:
            assert auth_data["user"]
            assert "password" not in auth_data


async def run_transfer_and_verify(
    client: AsyncClient,
    user: MockUser,
    transfer_id: int,
    source_auth: str = "basic",
    target_auth: str = "basic",
) -> dict[str, Any]:
    response = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": transfer_id},
    )
    assert response.status_code == 200, response.text

    run_data = await get_run_on_end(
        client=client,
        run_id=response.json()["id"],
        token=user.token,
    )
    assert run_data["status"] == Status.FINISHED.value
    assert "correlation_id" in run_data["log_url"]
    assert "run_id" in run_data["log_url"]
    verify_transfer_auth_data(run_data, source_auth, target_auth)

    return run_data


def cast_dataframe_types(df: DataFrame, init_df: DataFrame) -> tuple[DataFrame, DataFrame]:
    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    return df, init_df


def truncate_datetime_to_seconds(
    df: DataFrame,
    init_df: DataFrame,
    transfer_direction: str | None = None,
) -> tuple[DataFrame, DataFrame]:
    # Excel does not support datetime values with precision greater than milliseconds
    # Spark rounds datetime to nearest 3.33 milliseconds when writing to MSSQL: https://onetl.readthedocs.io/en/latest/connection/db_connection/mssql/types.html#id5
    if transfer_direction == "file_to_db" or transfer_direction is None:
        df = df.withColumn("REGISTERED_AT", date_trunc("second", col("REGISTERED_AT")))
        init_df = init_df.withColumn("REGISTERED_AT", date_trunc("second", col("REGISTERED_AT")))
    elif transfer_direction == "db_to_file":
        init_df = init_df.withColumn(
            "REGISTERED_AT",
            to_timestamp(date_format(col("REGISTERED_AT"), "yyyy-MM-dd HH:mm:ss.SSS")),
        )
    return df, init_df


def round_datetime_to_seconds(df: DataFrame, init_df: DataFrame) -> tuple[DataFrame, DataFrame]:
    # Spark rounds milliseconds to seconds while writing to MySQL: https://onetl.readthedocs.io/en/latest/connection/db_connection/mysql/types.html#id5
    df = df.withColumn(
        "REGISTERED_AT",
        from_unixtime((col("REGISTERED_AT").cast("double") + 0.5).cast("long")).cast("timestamp"),
    )
    init_df = init_df.withColumn(
        "REGISTERED_AT",
        from_unixtime((col("REGISTERED_AT").cast("double") + 0.5).cast("long")).cast("timestamp"),
    )
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


def verify_file_name_template(file_names: list[str], expected_extension: str) -> None:
    for file_name in file_names:
        run_created_at, index_and_extension = file_name.split("-")
        assert len(run_created_at.split("_")) == 6, f"Got wrong {run_created_at=}"
        assert index_and_extension.split(".", 1)[1] == expected_extension


def split_df(df: DataFrame, ratio: float, keep_sorted_by: str) -> tuple[DataFrame, DataFrame]:
    first_df = df.limit(int(df.count() * ratio))
    second_df = df.subtract(first_df).sort(keep_sorted_by)
    return first_df, second_df
