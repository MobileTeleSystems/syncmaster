import secrets

import pytest
import pytest_asyncio
from httpx import AsyncClient
from onetl.db import DBReader
from pyspark.sql import DataFrame, SparkSession
from pytest_lazy_fixtures import lf
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Group, Queue, Transfer
from tests.mocks import MockUser
from tests.test_unit.utils import create_transfer
from tests.utils import (
    cast_dataframe_types,
    run_transfer_and_verify,
    split_df,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.worker]


@pytest_asyncio.fixture
async def postgres_to_iceberg_rest_s3(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    iceberg_rest_s3_connection: Connection,
    postgres_connection: Connection,
    strategy: dict,
    transformations: list[dict],
):
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"postgres_to_iceberg_rest_s3_{secrets.token_hex(5)}",
        source_connection_id=postgres_connection.id,
        target_connection_id=iceberg_rest_s3_connection.id,
        source_params={
            "type": "postgres",
            "table_name": "public.source_table",
        },
        target_params={
            "type": "iceberg_rest_s3",
            "table_name": "default.target_table",
            "catalog_name": "iceberg_rest_s3",
        },
        strategy_params=strategy,
        transformations=transformations,
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture
async def iceberg_rest_s3_to_postgres(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    iceberg_rest_s3_connection: Connection,
    postgres_connection: Connection,
    strategy: dict,
    transformations: list[dict],
):
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"iceberg_rest_s3_to_postgres_{secrets.token_hex(5)}",
        source_connection_id=iceberg_rest_s3_connection.id,
        target_connection_id=postgres_connection.id,
        source_params={
            "type": "iceberg_rest_s3",
            "table_name": "default.source_table",
            "catalog_name": "iceberg_rest_s3",
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
async def test_run_transfer_postgres_to_iceberg_rest_s3_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_iceberg_rest_s3,
    init_df: DataFrame,
    postgres_to_iceberg_rest_s3: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df)
    iceberg, _ = prepare_iceberg_rest_s3

    await run_transfer_and_verify(
        client,
        group_owner,
        postgres_to_iceberg_rest_s3.id,
        target_auth="iceberg_rest_basic_s3_basic",
    )

    reader = DBReader(
        connection=iceberg,
        table="default.target_table",
    )
    df = reader.run()

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
async def test_run_transfer_postgres_to_iceberg_rest_s3_mixed_naming_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_iceberg_rest_s3,
    init_df_with_mixed_column_naming: DataFrame,
    postgres_to_iceberg_rest_s3: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df_with_mixed_column_naming)
    iceberg, _ = prepare_iceberg_rest_s3

    await run_transfer_and_verify(
        client,
        group_owner,
        postgres_to_iceberg_rest_s3.id,
        target_auth="iceberg_rest_basic_s3_basic",
    )

    reader = DBReader(
        connection=iceberg,
        table="default.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    df, init_df_with_mixed_column_naming = cast_dataframe_types(df, init_df_with_mixed_column_naming)
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
async def test_run_transfer_postgres_to_iceberg_rest_s3_with_incremental_strategy(
    spark: SparkSession,
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_iceberg_rest_s3,
    init_df: DataFrame,
    postgres_to_iceberg_rest_s3: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    iceberg, _ = prepare_iceberg_rest_s3

    first_transfer_df, second_transfer_df = split_df(df=init_df, ratio=0.6, keep_sorted_by="number")
    fill_with_data(first_transfer_df)
    await run_transfer_and_verify(
        client,
        group_owner,
        postgres_to_iceberg_rest_s3.id,
        target_auth="iceberg_rest_basic_s3_basic",
    )

    reader = DBReader(
        connection=iceberg,
        table="default.target_table",
    )
    df = reader.run()

    df, first_transfer_df = cast_dataframe_types(df, first_transfer_df)
    assert df.sort("ID").collect() == first_transfer_df.sort("ID").collect()

    fill_with_data(second_transfer_df)
    await run_transfer_and_verify(
        client,
        group_owner,
        postgres_to_iceberg_rest_s3.id,
        target_auth="iceberg_rest_basic_s3_basic",
    )

    spark.catalog.refreshTable("iceberg_rest_s3.default.target_table")
    df_with_increment = reader.run()
    df_with_increment, init_df = cast_dataframe_types(df_with_increment, init_df)
    assert df_with_increment.sort("ID").collect() == init_df.sort("ID").collect()


@pytest.mark.parametrize(
    "source_type, strategy, transformations, expected_filter",
    [
        (
            "iceberg_rest_s3",
            lf("full_strategy"),
            lf("dataframe_rows_filter_transformations"),
            lf("expected_dataframe_rows_filter"),
        ),
        (
            "iceberg_rest_s3",
            lf("full_strategy"),
            lf("dataframe_columns_filter_transformations"),
            lf("expected_dataframe_columns_filter"),
        ),
    ],
)
async def test_run_transfer_iceberg_rest_s3_to_postgres_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_iceberg_rest_s3,
    prepare_postgres,
    init_df: DataFrame,
    iceberg_rest_s3_to_postgres: Transfer,
    source_type,
    strategy,
    transformations,
    expected_filter,
):
    _, fill_with_data = prepare_iceberg_rest_s3
    fill_with_data(init_df)
    postgres, _ = prepare_postgres
    init_df = expected_filter(init_df, source_type)

    await run_transfer_and_verify(
        client,
        group_owner,
        iceberg_rest_s3_to_postgres.id,
        source_auth="iceberg_rest_basic_s3_basic",
    )

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

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
async def test_run_transfer_iceberg_rest_s3_to_postgres_mixes_naming_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_iceberg_rest_s3,
    prepare_postgres,
    init_df_with_mixed_column_naming: DataFrame,
    iceberg_rest_s3_to_postgres: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_iceberg_rest_s3
    fill_with_data(init_df_with_mixed_column_naming)
    postgres, _ = prepare_postgres

    await run_transfer_and_verify(
        client,
        group_owner,
        iceberg_rest_s3_to_postgres.id,
        source_auth="iceberg_rest_basic_s3_basic",
    )

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    df, init_df_with_mixed_column_naming = cast_dataframe_types(df, init_df_with_mixed_column_naming)
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
async def test_run_transfer_iceberg_rest_s3_to_postgres_with_incremental_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_iceberg_rest_s3,
    prepare_postgres,
    init_df: DataFrame,
    iceberg_rest_s3_to_postgres: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_iceberg_rest_s3
    postgres, _ = prepare_postgres

    first_transfer_df, second_transfer_df = split_df(df=init_df, ratio=0.6, keep_sorted_by="number")
    fill_with_data(first_transfer_df)
    await run_transfer_and_verify(
        client,
        group_owner,
        iceberg_rest_s3_to_postgres.id,
        source_auth="iceberg_rest_basic_s3_basic",
    )

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    df, first_transfer_df = cast_dataframe_types(df, first_transfer_df)
    assert df.sort("ID").collect() == first_transfer_df.sort("ID").collect()

    fill_with_data(second_transfer_df)
    await run_transfer_and_verify(
        client,
        group_owner,
        iceberg_rest_s3_to_postgres.id,
        source_auth="iceberg_rest_basic_s3_basic",
    )

    df_with_increment = reader.run()
    df_with_increment, init_df = cast_dataframe_types(df_with_increment, init_df)
    assert df_with_increment.sort("ID").collect() == init_df.sort("ID").collect()
