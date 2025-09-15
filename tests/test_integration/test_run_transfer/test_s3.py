import os
import secrets

import pytest
import pytest_asyncio
from httpx import AsyncClient
from onetl.connection import S3, SparkS3
from onetl.db import DBReader
from onetl.file import FileDFReader
from pyspark.sql import DataFrame
from pytest_lazy_fixtures import lf
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Group, Queue
from syncmaster.db.models.transfer import Transfer
from tests.mocks import MockUser
from tests.test_unit.utils import create_transfer
from tests.utils import (
    cast_dataframe_types,
    run_transfer_and_verify,
    split_df,
    truncate_datetime_to_seconds,
    verify_file_name_template,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.worker]


@pytest_asyncio.fixture
async def s3_to_postgres(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    init_df: DataFrame,
    s3_connection: Connection,
    postgres_connection: Connection,
    prepare_s3,
    source_file_format,
    file_format_flavor: str,
    transformations: list[dict],
):
    format_name, file_format = source_file_format
    format_name_in_path = "xlsx" if format_name == "excel" else format_name
    _, source_path, _ = prepare_s3

    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"s32postgres_{secrets.token_hex(5)}",
        source_connection_id=s3_connection.id,
        target_connection_id=postgres_connection.id,
        source_params={
            "type": "s3",
            "directory_path": os.fspath(source_path / "file_df_connection" / format_name_in_path / file_format_flavor),
            "file_format": {
                "type": format_name,
                **file_format.dict(),
            },
            "df_schema": init_df.schema.json(),
            "options": {},
        },
        target_params={
            "type": "postgres",
            "table_name": "public.target_table",
        },
        transformations=transformations,
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture(params=[""])
async def postgres_to_s3(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    s3_connection: Connection,
    postgres_connection: Connection,
    target_file_format,
    file_format_flavor: str,
    strategy: dict,
    transformations: list[dict],
):
    format_name, file_format = target_file_format
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"postgres2s3_{secrets.token_hex(5)}",
        source_connection_id=postgres_connection.id,
        target_connection_id=s3_connection.id,
        source_params={
            "type": "postgres",
            "table_name": "public.source_table",
        },
        target_params={
            "type": "s3",
            "directory_path": f"/target/{format_name}/{file_format_flavor}",
            "file_format": {
                "type": format_name,
                **file_format.dict(),
            },
            "file_name_template": "{run_created_at}-{index}.{extension}",
            "options": {},
        },
        strategy_params=strategy,
        transformations=transformations,
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest.mark.parametrize(
    "source_file_format, file_format_flavor, source_type, transformations, expected_filter",
    [
        pytest.param(
            ("csv", {}),
            "with_header",
            "s3",
            lf("dataframe_rows_filter_transformations"),
            lf("expected_dataframe_rows_filter"),
            id="csv",
        ),
        pytest.param(
            ("json", {}),
            "without_compression",
            "s3",
            lf("dataframe_columns_filter_transformations"),
            lf("expected_dataframe_columns_filter"),
            id="json",
        ),
        pytest.param(
            ("jsonline", {}),
            "without_compression",
            None,
            [],
            None,
            id="jsonline",
        ),
        pytest.param(
            ("excel", {}),
            "with_header",
            None,
            [],
            None,
            id="excel",
        ),
        pytest.param(
            ("orc", {}),
            "without_compression",
            None,
            [],
            None,
            id="orc",
        ),
        pytest.param(
            ("parquet", {}),
            "without_compression",
            None,
            [],
            None,
            id="parquet",
        ),
        pytest.param(
            ("xml", {}),
            "without_compression",
            None,
            [],
            None,
            id="xml",
        ),
    ],
    indirect=["source_file_format", "file_format_flavor"],
)
async def test_run_transfer_s3_to_postgres_with_full_strategy(
    prepare_postgres,
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    s3_to_postgres: Transfer,
    source_file_format,
    file_format_flavor,
    source_type,
    transformations,
    expected_filter,
):
    postgres, _ = prepare_postgres
    file_format, _ = source_file_format
    if expected_filter:
        init_df = expected_filter(init_df, source_type)

    await run_transfer_and_verify(client, group_owner, s3_to_postgres.id, source_auth="s3")

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    if file_format == "excel":
        df, init_df = truncate_datetime_to_seconds(df, init_df, transfer_direction="file_to_db")

    df, init_df = cast_dataframe_types(df, init_df)
    assert df.sort("id").collect() == init_df.sort("id").collect()


@pytest.mark.parametrize(
    "target_file_format, file_format_flavor, strategy, transformations, expected_extension",
    [
        pytest.param(
            ("csv", {"compression": "lz4"}),
            "with_compression",
            lf("full_strategy"),
            [],
            "csv.lz4",
            id="csv",
        ),
        pytest.param(
            ("jsonline", {}),
            "without_compression",
            lf("full_strategy"),
            [],
            "jsonl",
            id="jsonline",
        ),
        pytest.param(
            ("excel", {}),
            "with_header",
            lf("full_strategy"),
            [],
            "xlsx",
            id="excel",
        ),
        pytest.param(
            ("orc", {"compression": "none"}),
            "without_compression",
            lf("full_strategy"),
            [],
            "orc",
            id="orc",
        ),
        pytest.param(
            ("parquet", {"compression": "gzip"}),
            "with_compression",
            lf("full_strategy"),
            [],
            "gz.parquet",
            id="parquet",
        ),
        pytest.param(
            ("xml", {"compression": "none"}),
            "without_compression",
            lf("full_strategy"),
            [],
            "xml",
            id="xml",
        ),
    ],
    indirect=["target_file_format", "file_format_flavor"],
)
async def test_run_transfer_postgres_to_s3_with_full_strategy(
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    s3_file_df_connection: SparkS3,
    s3_file_connection: S3,
    prepare_postgres,
    prepare_s3,
    postgres_to_s3: Transfer,
    target_file_format,
    file_format_flavor: str,
    strategy,
    transformations,
    expected_extension: str,
):
    format_name, format = target_file_format
    target_path = f"/target/{format_name}/{file_format_flavor}"
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df)

    await run_transfer_and_verify(client, group_owner, postgres_to_s3.id, target_auth="s3")

    files = [file.name for file in s3_file_connection.list_dir(target_path)]
    verify_file_name_template(files, expected_extension)

    reader = FileDFReader(
        connection=s3_file_df_connection,
        format=format,
        source_path=target_path,
        df_schema=init_df.schema,
        options={},
    )
    df = reader.run()

    if format_name == "excel":
        df, init_df = truncate_datetime_to_seconds(df, init_df, transfer_direction="db_to_file")

    df, init_df = cast_dataframe_types(df, init_df)
    assert df.sort("id").collect() == init_df.sort("id").collect()


@pytest.mark.parametrize(
    "target_file_format, file_format_flavor, strategy, transformations, expected_extension",
    [
        pytest.param(
            ("csv", {"compression": "lz4"}),
            "with_compression",
            lf("incremental_strategy_by_number_column"),
            [],
            "csv.lz4",
            id="csv",
        ),
    ],
    indirect=["target_file_format", "file_format_flavor"],
)
async def test_run_transfer_postgres_to_s3_with_incremental_strategy(
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    s3_file_df_connection: SparkS3,
    s3_file_connection: S3,
    prepare_postgres,
    prepare_s3,
    postgres_to_s3: Transfer,
    target_file_format,
    file_format_flavor: str,
    strategy,
    transformations,
    expected_extension: str,
):
    format_name, format = target_file_format
    target_path = f"/target/{format_name}/{file_format_flavor}"
    _, fill_with_data = prepare_postgres

    first_transfer_df, second_transfer_df = split_df(df=init_df, ratio=0.6, keep_sorted_by="number")
    fill_with_data(first_transfer_df)
    await run_transfer_and_verify(client, group_owner, postgres_to_s3.id, target_auth="s3")

    files = [file.name for file in s3_file_connection.list_dir(target_path)]
    verify_file_name_template(files, expected_extension)

    reader = FileDFReader(
        connection=s3_file_df_connection,
        format=format,
        source_path=target_path,
        df_schema=init_df.schema,
        options={},
    )
    df = reader.run()

    df, first_transfer_df = cast_dataframe_types(df, first_transfer_df)
    assert df.sort("id").collect() == first_transfer_df.sort("id").collect()

    fill_with_data(second_transfer_df)
    await run_transfer_and_verify(client, group_owner, postgres_to_s3.id, target_auth="s3")

    files = [file.name for file in s3_file_connection.list_dir(target_path)]
    verify_file_name_template(files, expected_extension)

    df_with_increment = reader.run()
    df_with_increment, init_df = cast_dataframe_types(df_with_increment, init_df)
    assert df_with_increment.sort("id").collect() == init_df.sort("id").collect()
