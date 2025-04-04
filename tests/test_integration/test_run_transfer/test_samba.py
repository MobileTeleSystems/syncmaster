import os
import secrets
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient
from onetl.connection import Samba, SparkLocalFS
from onetl.db import DBReader
from onetl.file import FileDFReader, FileDownloader
from pyspark.sql import DataFrame
from pytest_lazy_fixtures import lf
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Group, Queue
from syncmaster.db.models.transfer import Transfer
from tests.mocks import MockUser
from tests.test_unit.utils import create_transfer
from tests.utils import (
    add_increment_to_files_and_upload,
    cast_dataframe_types,
    run_transfer_and_verify,
    split_df,
    verify_file_name_template,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.worker]


@pytest_asyncio.fixture
async def samba_to_postgres(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    init_df: DataFrame,
    samba_connection: Connection,
    postgres_connection: Connection,
    prepare_samba,
    source_file_format,
    file_format_flavor: str,
    strategy: dict,
):
    format_name, file_format = source_file_format
    format_name_in_path = "xlsx" if format_name == "excel" else format_name
    _, source_path, _ = prepare_samba

    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"samba2postgres_{secrets.token_hex(5)}",
        source_connection_id=samba_connection.id,
        target_connection_id=postgres_connection.id,
        source_params={
            "type": "samba",
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
        strategy_params=strategy,
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture(params=[""])
async def postgres_to_samba(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    samba_connection: Connection,
    postgres_connection: Connection,
    target_file_format,
    file_format_flavor: str,
    strategy: dict,
):
    format_name, file_format = target_file_format
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"postgres2samba_{secrets.token_hex(5)}",
        source_connection_id=postgres_connection.id,
        target_connection_id=samba_connection.id,
        source_params={
            "type": "postgres",
            "table_name": "public.source_table",
        },
        target_params={
            "type": "samba",
            "directory_path": f"/target/{format_name}/{file_format_flavor}",
            "file_format": {
                "type": format_name,
                **file_format.dict(),
            },
            "file_name_template": "{run_created_at}-{index}.{extension}",
            "options": {},
        },
        strategy_params=strategy,
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest.mark.parametrize(
    "source_file_format, file_format_flavor, strategy",
    [
        pytest.param(
            ("csv", {}),
            "with_header",
            lf("full_strategy"),
            id="csv",
        ),
    ],
    indirect=["source_file_format", "file_format_flavor"],
)
async def test_run_transfer_samba_to_postgres_with_full_strategy(
    prepare_postgres,
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    samba_to_postgres: Transfer,
    source_file_format: tuple[str, dict],
    file_format_flavor: str,
    strategy: dict,
):
    postgres, _ = prepare_postgres
    file_format, _ = source_file_format

    await run_transfer_and_verify(client, group_owner, samba_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    df, init_df = cast_dataframe_types(df, init_df)
    assert df.sort("id").collect() == init_df.sort("id").collect()


@pytest.mark.parametrize(
    "source_file_format, file_format_flavor, strategy",
    [
        pytest.param(
            ("csv", {}),
            "with_header",
            lf("incremental_strategy_by_file_name"),
            id="csv",
        ),
    ],
    indirect=["source_file_format", "file_format_flavor"],
)
async def test_run_transfer_samba_to_postgres_with_incremental_strategy(
    prepare_postgres,
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    samba_to_postgres: Transfer,
    samba_file_connection: Samba,
    source_file_format: tuple[str, dict],
    file_format_flavor: str,
    strategy: dict,
    tmp_path: Path,
):
    postgres, _ = prepare_postgres
    file_format, _ = source_file_format

    await run_transfer_and_verify(client, group_owner, samba_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    df, init_df = cast_dataframe_types(df, init_df)
    assert df.sort("id").collect() == init_df.sort("id").collect()

    add_increment_to_files_and_upload(
        file_connection=samba_file_connection,
        remote_path=f"/data/file_df_connection/{file_format}/{file_format_flavor}",
        tmp_path=tmp_path,
    )

    await run_transfer_and_verify(client, group_owner, samba_to_postgres.id)

    df_with_increment = reader.run()
    df_with_increment, init_df = cast_dataframe_types(df_with_increment, init_df)
    assert df_with_increment.sort("id").collect() == init_df.union(init_df).sort("id").collect()


@pytest.mark.parametrize(
    "target_file_format, file_format_flavor, expected_extension, strategy",
    [
        pytest.param(
            ("csv", {"compression": "lz4"}),
            "with_compression",
            "csv.lz4",
            lf("full_strategy"),
            id="csv",
        ),
    ],
    indirect=["target_file_format", "file_format_flavor"],
)
async def test_run_transfer_postgres_to_samba_with_full_strategy(
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    prepare_postgres,
    samba_file_connection_with_path,
    samba_file_connection: Samba,
    samba_file_df_connection: SparkLocalFS,
    postgres_to_samba: Transfer,
    target_file_format,
    file_format_flavor: str,
    tmp_path: Path,
    expected_extension: str,
    strategy: dict,
):
    format_name, format = target_file_format
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df)

    await run_transfer_and_verify(client, group_owner, postgres_to_samba.id)

    downloader = FileDownloader(
        connection=samba_file_connection,
        source_path=f"/target/{format_name}/{file_format_flavor}",
        local_path=tmp_path,
    )
    downloader.run()

    verify_file_name_template(os.listdir(tmp_path), expected_extension)

    reader = FileDFReader(
        connection=samba_file_df_connection,
        format=format,
        source_path=tmp_path,
        df_schema=init_df.schema,
    )
    df = reader.run()

    df, init_df = cast_dataframe_types(df, init_df)
    assert df.sort("id").collect() == init_df.sort("id").collect()


@pytest.mark.parametrize(
    "target_file_format, file_format_flavor, expected_extension, strategy",
    [
        pytest.param(
            ("csv", {"compression": "lz4"}),
            "with_compression",
            "csv.lz4",
            lf("incremental_strategy_by_number_column"),
            id="csv",
        ),
    ],
    indirect=["target_file_format", "file_format_flavor"],
)
async def test_run_transfer_postgres_to_samba_with_incremental_strategy(
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    prepare_postgres,
    samba_file_connection_with_path,
    samba_file_connection: Samba,
    samba_file_df_connection: SparkLocalFS,
    postgres_to_samba: Transfer,
    target_file_format,
    file_format_flavor: str,
    tmp_path: Path,
    expected_extension: str,
    strategy: dict,
):
    format_name, format = target_file_format
    _, fill_with_data = prepare_postgres

    first_transfer_df, second_transfer_df = split_df(df=init_df, ratio=0.6, keep_sorted_by="number")
    fill_with_data(first_transfer_df)

    await run_transfer_and_verify(client, group_owner, postgres_to_samba.id)

    downloader = FileDownloader(
        connection=samba_file_connection,
        source_path=f"/target/{format_name}/{file_format_flavor}",
        local_path=tmp_path,
    )
    downloader.run()

    verify_file_name_template(os.listdir(tmp_path), expected_extension)

    reader = FileDFReader(
        connection=samba_file_df_connection,
        format=format,
        source_path=tmp_path,
        df_schema=init_df.schema,
    )
    df = reader.run()

    df, first_transfer_df = cast_dataframe_types(df, first_transfer_df)
    assert df.sort("id").collect() == first_transfer_df.sort("id").collect()

    fill_with_data(second_transfer_df)
    await run_transfer_and_verify(client, group_owner, postgres_to_samba.id)

    downloader.run()
    verify_file_name_template(os.listdir(tmp_path), expected_extension)

    df_with_increment = reader.run()
    df_with_increment, second_transfer_df = cast_dataframe_types(df_with_increment, second_transfer_df)
    assert df_with_increment.sort("id").collect() == init_df.sort("id").collect()
