import secrets

import pytest
import pytest_asyncio
from httpx import AsyncClient
from onetl.connection import MySQL
from onetl.db import DBReader
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, from_unixtime
from pytest_lazy_fixtures import lf
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Group, Queue, Transfer
from tests.mocks import MockUser
from tests.test_unit.utils import create_transfer
from tests.utils import (
    cast_dataframe_types,
    round_datetime_to_seconds,
    run_transfer_and_verify,
    split_df,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.worker]


@pytest_asyncio.fixture
async def postgres_to_mysql(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    mysql_for_conftest: MySQL,
    mysql_connection: Connection,
    postgres_connection: Connection,
    strategy: dict,
    transformations: list[dict],
):
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"postgres2mysql_{secrets.token_hex(5)}",
        source_connection_id=postgres_connection.id,
        target_connection_id=mysql_connection.id,
        source_params={
            "type": "postgres",
            "table_name": "public.source_table",
        },
        target_params={
            "type": "mysql",
            "table_name": f"{mysql_for_conftest.database_name}.target_table",
        },
        strategy_params=strategy,
        transformations=transformations,
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture
async def mysql_to_postgres(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    mysql_for_conftest: MySQL,
    mysql_connection: Connection,
    postgres_connection: Connection,
    strategy: dict,
    transformations: list[dict],
):
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"mysql2postgres_{secrets.token_hex(5)}",
        source_connection_id=mysql_connection.id,
        target_connection_id=postgres_connection.id,
        source_params={
            "type": "mysql",
            "table_name": f"{mysql_for_conftest.database_name}.source_table",
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
    "strategy, transformations",
    [
        (
            lf("full_strategy"),
            [],
        ),
    ],
)
async def test_run_transfer_postgres_to_mysql_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_mysql,
    init_df: DataFrame,
    postgres_to_mysql: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df)
    mysql, _ = prepare_mysql

    await run_transfer_and_verify(client, group_owner, postgres_to_mysql.id)

    reader = DBReader(
        connection=mysql,
        table=f"{mysql.database}.target_table",
    )
    df = reader.run()

    df, init_df = round_datetime_to_seconds(df, init_df)
    df, init_df = cast_dataframe_types(df, init_df)
    assert df.sort("ID").collect() == init_df.sort("ID").collect()


@pytest.mark.parametrize(
    "strategy, transformations",
    [
        (
            lf("full_strategy"),
            [],
        ),
    ],
)
async def test_run_transfer_postgres_to_mysql_mixed_naming_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_mysql,
    init_df_with_mixed_column_naming: DataFrame,
    postgres_to_mysql: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df_with_mixed_column_naming)
    mysql, _ = prepare_mysql

    await run_transfer_and_verify(client, group_owner, postgres_to_mysql.id)

    reader = DBReader(
        connection=mysql,
        table=f"{mysql.database}.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    # as Spark rounds milliseconds to seconds while writing to mysql: https://onetl.readthedocs.io/en/latest/connection/db_connection/mysql/types.html#id5
    df = df.withColumn(
        "Registered At",
        from_unixtime((col("Registered At").cast("double") + 0.5).cast("long")).cast("timestamp"),
    )
    init_df_with_mixed_column_naming = init_df_with_mixed_column_naming.withColumn(
        "Registered At",
        from_unixtime((col("Registered At").cast("double") + 0.5).cast("long")).cast("timestamp"),
    )
    for field in init_df_with_mixed_column_naming.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("ID").collect() == init_df_with_mixed_column_naming.sort("ID").collect()


@pytest.mark.parametrize(
    "strategy, transformations",
    [
        (
            lf("incremental_strategy_by_number_column"),
            [],
        ),
    ],
)
async def test_run_transfer_postgres_to_mysql_with_incremental_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_mysql,
    init_df: DataFrame,
    postgres_to_mysql: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    mysql, _ = prepare_mysql

    first_transfer_df, second_transfer_df = split_df(df=init_df, ratio=0.6, keep_sorted_by="number")
    fill_with_data(first_transfer_df)
    await run_transfer_and_verify(client, group_owner, postgres_to_mysql.id)

    reader = DBReader(
        connection=mysql,
        table=f"{mysql.database}.target_table",
    )
    df = reader.run()

    df, first_transfer_df = round_datetime_to_seconds(df, first_transfer_df)
    df, first_transfer_df = cast_dataframe_types(df, first_transfer_df)
    assert df.sort("ID").collect() == first_transfer_df.sort("ID").collect()

    fill_with_data(second_transfer_df)
    await run_transfer_and_verify(client, group_owner, postgres_to_mysql.id)

    df_with_increment = reader.run()
    df_with_increment, init_df = round_datetime_to_seconds(df_with_increment, init_df)
    df_with_increment, init_df = cast_dataframe_types(df_with_increment, init_df)
    assert df_with_increment.sort("ID").collect() == init_df.sort("ID").collect()


@pytest.mark.parametrize(
    "source_type, strategy, transformations, expected_filter",
    [
        (
            "mysql",
            lf("full_strategy"),
            lf("dataframe_rows_filter_transformations"),
            lf("expected_dataframe_rows_filter"),
        ),
        (
            "mysql",
            lf("full_strategy"),
            lf("dataframe_columns_filter_transformations"),
            lf("expected_dataframe_columns_filter"),
        ),
    ],
)
async def test_run_transfer_mysql_to_postgres_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_mysql,
    prepare_postgres,
    init_df: DataFrame,
    mysql_to_postgres: Transfer,
    source_type,
    strategy,
    transformations,
    expected_filter,
):
    _, fill_with_data = prepare_mysql
    fill_with_data(init_df)
    postgres, _ = prepare_postgres
    init_df = expected_filter(init_df, source_type)

    await run_transfer_and_verify(client, group_owner, mysql_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    df, init_df = round_datetime_to_seconds(df, init_df)
    df, init_df = cast_dataframe_types(df, init_df)
    assert df.sort("ID").collect() == init_df.sort("ID").collect()


@pytest.mark.parametrize(
    "strategy, transformations",
    [
        (
            lf("full_strategy"),
            [],
        ),
    ],
)
async def test_run_transfer_mysql_to_postgres_mixed_naming_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_mysql,
    prepare_postgres,
    init_df_with_mixed_column_naming: DataFrame,
    mysql_to_postgres: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_mysql
    fill_with_data(init_df_with_mixed_column_naming)
    postgres, _ = prepare_postgres

    await run_transfer_and_verify(client, group_owner, mysql_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    # as Spark rounds milliseconds to seconds while writing to mysql: https://onetl.readthedocs.io/en/latest/connection/db_connection/mysql/types.html#id5
    df = df.withColumn(
        "Registered At",
        from_unixtime((col("Registered At").cast("double") + 0.5).cast("long")).cast("timestamp"),
    )
    init_df_with_mixed_column_naming = init_df_with_mixed_column_naming.withColumn(
        "Registered At",
        from_unixtime((col("Registered At").cast("double") + 0.5).cast("long")).cast("timestamp"),
    )
    for field in init_df_with_mixed_column_naming.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("ID").collect() == init_df_with_mixed_column_naming.sort("ID").collect()


@pytest.mark.parametrize(
    "strategy, transformations",
    [
        (
            lf("incremental_strategy_by_number_column"),
            [],
        ),
    ],
)
async def test_run_transfer_mysql_to_postgres_with_incremental_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_mysql,
    prepare_postgres,
    init_df: DataFrame,
    mysql_to_postgres: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_mysql
    postgres, _ = prepare_postgres

    first_transfer_df, second_transfer_df = split_df(df=init_df, ratio=0.6, keep_sorted_by="number")
    fill_with_data(first_transfer_df)
    await run_transfer_and_verify(client, group_owner, mysql_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    df, first_transfer_df = round_datetime_to_seconds(df, first_transfer_df)
    df, first_transfer_df = cast_dataframe_types(df, first_transfer_df)
    assert df.sort("ID").collect() == first_transfer_df.sort("ID").collect()

    fill_with_data(second_transfer_df)
    await run_transfer_and_verify(client, group_owner, mysql_to_postgres.id)

    df_with_increment = reader.run()
    df_with_increment, init_df = round_datetime_to_seconds(df_with_increment, init_df)
    df_with_increment, init_df = cast_dataframe_types(df_with_increment, init_df)
    assert df_with_increment.sort("ID").collect() == init_df.sort("ID").collect()
