import secrets

import pytest
import pytest_asyncio
from httpx import AsyncClient
from onetl.connection import MSSQL
from onetl.db import DBReader
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, date_trunc
from pytest_lazy_fixtures import lf
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Group, Queue, Transfer
from tests.mocks import MockUser
from tests.test_unit.utils import create_transfer
from tests.utils import (
    cast_dataframe_types,
    run_transfer_and_verify,
    split_df,
    truncate_datetime_to_seconds,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.worker]


@pytest_asyncio.fixture
async def postgres_to_mssql(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    mssql_for_conftest: MSSQL,
    mssql_connection: Connection,
    postgres_connection: Connection,
    strategy: dict,
    transformations: list[dict],
):
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"postgres2mssql_{secrets.token_hex(5)}",
        source_connection_id=postgres_connection.id,
        target_connection_id=mssql_connection.id,
        source_params={
            "type": "postgres",
            "table_name": "public.source_table",
        },
        target_params={
            "type": "mssql",
            "table_name": "dbo.target_table",
        },
        strategy_params=strategy,
        transformations=transformations,
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture
async def mssql_to_postgres(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    mssql_for_conftest: MSSQL,
    mssql_connection: Connection,
    postgres_connection: Connection,
    strategy: dict,
    transformations: list[dict],
):
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"mssql2postgres_{secrets.token_hex(5)}",
        source_connection_id=mssql_connection.id,
        target_connection_id=postgres_connection.id,
        source_params={
            "type": "mssql",
            "table_name": "dbo.source_table",
        },
        target_params={
            "type": "postgres",
            "table_name": "public.target_table",
        },
        strategy_params=strategy,
        transformations=transformations,
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest.mark.parametrize(
    ["strategy", "transformations"],
    [
        (
            lf("full_strategy"),
            [],
        ),
    ],
)
async def test_run_transfer_postgres_to_mssql_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_mssql,
    init_df: DataFrame,
    postgres_to_mssql: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df)
    mssql, _ = prepare_mssql

    await run_transfer_and_verify(client, group_owner, postgres_to_mssql.id)

    reader = DBReader(
        connection=mssql,
        table="dbo.target_table",
    )
    df = reader.run()

    df, init_df = truncate_datetime_to_seconds(df, init_df)
    df, init_df = cast_dataframe_types(df, init_df)
    assert df.sort("ID").collect() == init_df.sort("ID").collect()


@pytest.mark.parametrize(
    ["strategy", "transformations"],
    [
        (
            lf("full_strategy"),
            [],
        ),
    ],
)
async def test_run_transfer_postgres_to_mssql_mixed_naming_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_mssql,
    init_df_with_mixed_column_naming: DataFrame,
    postgres_to_mssql: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df_with_mixed_column_naming)
    mssql, _ = prepare_mssql

    await run_transfer_and_verify(client, group_owner, postgres_to_mssql.id)

    reader = DBReader(
        connection=mssql,
        table="dbo.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    # as Spark rounds datetime to nearest 3.33 milliseconds when writing to mssql: https://onetl.readthedocs.io/en/latest/connection/db_connection/mssql/types.html#id5
    df = df.withColumn("Registered At", date_trunc("second", col("Registered At")))
    init_df_with_mixed_column_naming = init_df_with_mixed_column_naming.withColumn(
        "Registered At",
        date_trunc("second", col("Registered At")),
    )

    for field in init_df_with_mixed_column_naming.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("ID").collect() == init_df_with_mixed_column_naming.sort("ID").collect()


@pytest.mark.parametrize(
    ["strategy", "transformations"],
    [
        (
            lf("incremental_strategy_by_number_column"),
            [],
        ),
    ],
)
async def test_run_transfer_postgres_to_mssql_with_incremental_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_mssql,
    init_df: DataFrame,
    postgres_to_mssql: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    mssql, _ = prepare_mssql

    first_transfer_df, second_transfer_df = split_df(df=init_df, ratio=0.6, keep_sorted_by="number")
    fill_with_data(first_transfer_df)
    await run_transfer_and_verify(client, group_owner, postgres_to_mssql.id)

    reader = DBReader(
        connection=mssql,
        table="dbo.target_table",
    )
    df = reader.run()

    df, first_transfer_df = truncate_datetime_to_seconds(df, first_transfer_df)
    df, first_transfer_df = cast_dataframe_types(df, first_transfer_df)
    assert df.sort("ID").collect() == first_transfer_df.sort("ID").collect()

    fill_with_data(second_transfer_df)
    await run_transfer_and_verify(client, group_owner, postgres_to_mssql.id)

    df_with_increment = reader.run()
    df_with_increment, init_df = truncate_datetime_to_seconds(df_with_increment, init_df)
    df_with_increment, init_df = cast_dataframe_types(df_with_increment, init_df)
    assert df_with_increment.sort("ID").collect() == init_df.sort("ID").collect()


@pytest.mark.parametrize(
    ["source_type", "strategy", "transformations", "expected_filter"],
    [
        (
            "mssql",
            lf("full_strategy"),
            lf("dataframe_rows_filter_transformations"),
            lf("expected_dataframe_rows_filter"),
        ),
        (
            "mssql",
            lf("full_strategy"),
            lf("dataframe_columns_filter_transformations"),
            lf("expected_dataframe_columns_filter"),
        ),
    ],
)
async def test_run_transfer_mssql_to_postgres_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_mssql,
    prepare_postgres,
    init_df: DataFrame,
    mssql_to_postgres: Transfer,
    source_type,
    strategy,
    transformations,
    expected_filter,
):
    _, fill_with_data = prepare_mssql
    fill_with_data(init_df)
    postgres, _ = prepare_postgres
    init_df = expected_filter(init_df, source_type)

    await run_transfer_and_verify(client, group_owner, mssql_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    df, init_df = truncate_datetime_to_seconds(df, init_df)
    df, init_df = cast_dataframe_types(df, init_df)
    assert df.sort("ID").collect() == init_df.sort("ID").collect()


@pytest.mark.parametrize(
    ["strategy", "transformations"],
    [
        (
            lf("full_strategy"),
            [],
        ),
    ],
)
async def test_run_transfer_mssql_to_postgres_mixed_naming_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_mssql,
    prepare_postgres,
    init_df_with_mixed_column_naming: DataFrame,
    mssql_to_postgres: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_mssql
    fill_with_data(init_df_with_mixed_column_naming)
    postgres, _ = prepare_postgres

    await run_transfer_and_verify(client, group_owner, mssql_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    # as Spark rounds datetime to nearest 3.33 milliseconds when writing to mssql: https://onetl.readthedocs.io/en/latest/connection/db_connection/mssql/types.html#id5
    df = df.withColumn("Registered At", date_trunc("second", col("Registered At")))
    init_df_with_mixed_column_naming = init_df_with_mixed_column_naming.withColumn(
        "Registered At",
        date_trunc("second", col("Registered At")),
    )

    for field in init_df_with_mixed_column_naming.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("ID").collect() == init_df_with_mixed_column_naming.sort("ID").collect()


@pytest.mark.parametrize(
    ["strategy", "transformations"],
    [
        (
            lf("incremental_strategy_by_number_column"),
            [],
        ),
    ],
)
async def test_run_transfer_mssql_to_postgres_with_incremental_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_mssql,
    prepare_postgres,
    init_df: DataFrame,
    mssql_to_postgres: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_mssql
    postgres, _ = prepare_postgres

    first_transfer_df, second_transfer_df = split_df(df=init_df, ratio=0.6, keep_sorted_by="number")
    fill_with_data(first_transfer_df)
    await run_transfer_and_verify(client, group_owner, mssql_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    df, first_transfer_df = truncate_datetime_to_seconds(df, first_transfer_df)
    df, first_transfer_df = cast_dataframe_types(df, first_transfer_df)
    assert df.sort("ID").collect() == first_transfer_df.sort("ID").collect()

    fill_with_data(second_transfer_df)
    await run_transfer_and_verify(client, group_owner, mssql_to_postgres.id)

    df_with_increment = reader.run()
    df_with_increment, init_df = truncate_datetime_to_seconds(df_with_increment, init_df)
    df_with_increment, init_df = cast_dataframe_types(df_with_increment, init_df)
    assert df_with_increment.sort("ID").collect() == init_df.sort("ID").collect()
