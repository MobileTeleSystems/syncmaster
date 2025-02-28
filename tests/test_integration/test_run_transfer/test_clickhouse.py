import secrets

import pytest
import pytest_asyncio
from httpx import AsyncClient
from onetl.connection import Clickhouse
from onetl.db import DBReader
from pyspark.sql import DataFrame
from pytest_lazy_fixtures import lf
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Group, Queue, Transfer
from tests.mocks import MockUser
from tests.test_unit.utils import create_transfer
from tests.utils import (
    prepare_dataframes_for_comparison,
    run_transfer_and_verify,
    split_df,
)

pytestmark = [pytest.mark.asyncio, pytest.mark.worker]


@pytest_asyncio.fixture
async def postgres_to_clickhouse(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    clickhouse_for_conftest: Clickhouse,
    clickhouse_connection: Connection,
    postgres_connection: Connection,
    strategy: dict,
    transformations: list[dict],
):
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"postgres2clickhouse_{secrets.token_hex(5)}",
        source_connection_id=postgres_connection.id,
        target_connection_id=clickhouse_connection.id,
        source_params={
            "type": "postgres",
            "table_name": "public.source_table",
        },
        target_params={
            "type": "clickhouse",
            "table_name": f"{clickhouse_for_conftest.user}.target_table",
        },
        strategy_params=strategy,
        transformations=transformations,
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture
async def clickhouse_to_postgres(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    clickhouse_for_conftest: Clickhouse,
    clickhouse_connection: Connection,
    postgres_connection: Connection,
    strategy: dict,
    transformations: list[dict],
):
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"clickhouse2postgres_{secrets.token_hex(5)}",
        source_connection_id=clickhouse_connection.id,
        target_connection_id=postgres_connection.id,
        source_params={
            "type": "clickhouse",
            "table_name": f"{clickhouse_for_conftest.user}.source_table",
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
    "source_type, strategy, transformations, expected_filter",
    [
        (
            "postgres",
            lf("full_strategy"),
            lf("dataframe_rows_filter_transformations"),
            lf("expected_dataframe_rows_filter"),
        ),
        (
            "postgres",
            lf("full_strategy"),
            lf("dataframe_columns_filter_transformations"),
            lf("expected_dataframe_columns_filter"),
        ),
    ],
)
async def test_run_transfer_postgres_to_clickhouse_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_clickhouse,
    init_df: DataFrame,
    postgres_to_clickhouse: Transfer,
    source_type,
    strategy,
    transformations,
    expected_filter,
):
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df)
    clickhouse, _ = prepare_clickhouse
    init_df = expected_filter(init_df, source_type)

    await run_transfer_and_verify(client, group_owner, postgres_to_clickhouse.id)

    reader = DBReader(
        connection=clickhouse,
        table=f"{clickhouse.user}.target_table",
    )
    df = reader.run()

    df, init_df = prepare_dataframes_for_comparison(df, init_df)
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
async def test_run_transfer_postgres_to_clickhouse_mixed_naming_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_clickhouse,
    init_df_with_mixed_column_naming: DataFrame,
    postgres_to_clickhouse: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df_with_mixed_column_naming)
    clickhouse, _ = prepare_clickhouse

    await run_transfer_and_verify(client, group_owner, postgres_to_clickhouse.id)

    reader = DBReader(
        connection=clickhouse,
        table=f"{clickhouse.user}.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    df, init_df_with_mixed_column_naming = prepare_dataframes_for_comparison(df, init_df_with_mixed_column_naming)
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
async def test_run_transfer_postgres_to_clickhouse_with_incremental_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_clickhouse,
    init_df: DataFrame,
    postgres_to_clickhouse: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_postgres
    clickhouse, _ = prepare_clickhouse

    first_transfer_df, second_transfer_df = split_df(df=init_df, ratio=0.6, keep_sorted_by="number")
    fill_with_data(first_transfer_df)
    await run_transfer_and_verify(client, group_owner, postgres_to_clickhouse.id)

    reader = DBReader(
        connection=clickhouse,
        table=f"{clickhouse.user}.target_table",
    )
    df = reader.run()

    df, first_transfer_df = prepare_dataframes_for_comparison(df, first_transfer_df)
    assert df.sort("ID").collect() == first_transfer_df.sort("ID").collect()

    fill_with_data(second_transfer_df)
    await run_transfer_and_verify(client, group_owner, postgres_to_clickhouse.id)

    reader = DBReader(
        connection=clickhouse,
        table=f"{clickhouse.user}.target_table",
    )
    df_with_increment = reader.run()

    df_with_increment, init_df = prepare_dataframes_for_comparison(df_with_increment, init_df)
    assert df_with_increment.sort("ID").collect() == init_df.sort("ID").collect()


@pytest.mark.parametrize(
    "source_type, strategy, transformations, expected_filter",
    [
        (
            "clickhouse",
            lf("full_strategy"),
            lf("dataframe_rows_filter_transformations"),
            lf("expected_dataframe_rows_filter"),
        ),
        (
            "clickhouse",
            lf("full_strategy"),
            lf("dataframe_columns_filter_transformations"),
            lf("expected_dataframe_columns_filter"),
        ),
    ],
)
async def test_run_transfer_clickhouse_to_postgres_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_clickhouse,
    prepare_postgres,
    init_df: DataFrame,
    source_type,
    strategy,
    transformations,
    expected_filter,
    clickhouse_to_postgres: Transfer,
):
    _, fill_with_data = prepare_clickhouse
    fill_with_data(init_df)
    postgres, _ = prepare_postgres
    init_df = expected_filter(init_df, source_type)

    await run_transfer_and_verify(client, group_owner, clickhouse_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    df, init_df = prepare_dataframes_for_comparison(df, init_df)
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
async def test_run_transfer_clickhouse_to_postgres_mixed_naming_with_full_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_clickhouse,
    prepare_postgres,
    init_df_with_mixed_column_naming: DataFrame,
    clickhouse_to_postgres: Transfer,
    strategy,
    transformations,
):
    _, fill_with_data = prepare_clickhouse
    fill_with_data(init_df_with_mixed_column_naming)
    postgres, _ = prepare_postgres

    await run_transfer_and_verify(client, group_owner, clickhouse_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    df, init_df_with_mixed_column_naming = prepare_dataframes_for_comparison(df, init_df_with_mixed_column_naming)
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
async def test_run_transfer_clickhouse_to_postgres_with_incremental_strategy(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_clickhouse,
    prepare_postgres,
    init_df: DataFrame,
    strategy,
    transformations,
    clickhouse_to_postgres: Transfer,
):
    _, fill_with_data = prepare_clickhouse
    postgres, _ = prepare_postgres

    first_transfer_df, second_transfer_df = split_df(df=init_df, ratio=0.6, keep_sorted_by="number")
    fill_with_data(first_transfer_df)
    await run_transfer_and_verify(client, group_owner, clickhouse_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    df, first_transfer_df = prepare_dataframes_for_comparison(df, first_transfer_df)
    assert df.sort("ID").collect() == first_transfer_df.sort("ID").collect()

    fill_with_data(second_transfer_df)
    await run_transfer_and_verify(client, group_owner, clickhouse_to_postgres.id)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df_with_increment = reader.run()

    df_with_increment, init_df = prepare_dataframes_for_comparison(df_with_increment, init_df)
    assert df_with_increment.sort("ID").collect() == init_df.sort("ID").collect()
