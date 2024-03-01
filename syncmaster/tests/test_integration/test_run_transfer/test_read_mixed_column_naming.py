import pytest
from httpx import AsyncClient
from onetl.db import DBReader
from pyspark.sql import DataFrame
from tests.utils import MockUser, get_run_on_end

from app.db.models import Status, Transfer

pytestmark = [pytest.mark.asyncio, pytest.mark.worker, pytest.mark.oracle]


async def test_change_mixed_column_naming_to_oracle_default_case(
    client: AsyncClient,
    transfers_with_mixed_column_naming,
    prepare_oracle_with_mixed_column_naming,
    init_df_with_mixed_column_naming: DataFrame,
):
    # Arrange
    user: MockUser = transfers_with_mixed_column_naming["group_owner"]
    transfer: Transfer = transfers_with_mixed_column_naming["postgres_oracle"]

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": transfer.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=user.token,
    )
    assert run_data["status"] == Status.FINISHED.value
    reader = DBReader(
        connection=prepare_oracle_with_mixed_column_naming,
        table=f"{prepare_oracle_with_mixed_column_naming.user}.target_table",
        # TODO: после фикса бага https://jira.mts.ru/browse/DOP-8666 в onetl, пофиксить тесты
        columns=list(map(lambda x: f'"{x}"'.upper(), init_df_with_mixed_column_naming.columns)),
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.upper() for column in init_df_with_mixed_column_naming.columns]

    for field in init_df_with_mixed_column_naming.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.collect() == init_df_with_mixed_column_naming.collect()


async def test_change_mixed_column_naming_to_postgres_default_case(
    client: AsyncClient,
    transfers_with_mixed_column_naming,
    prepare_postgres_with_mixed_column_naming,
    init_df_with_mixed_column_naming: DataFrame,
):
    # Arrange
    user: MockUser = transfers_with_mixed_column_naming["group_owner"]
    transfer: Transfer = transfers_with_mixed_column_naming["oracle_postgres"]

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": transfer.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=user.token,
    )
    assert run_data["status"] == Status.FINISHED.value

    reader = DBReader(
        connection=prepare_postgres_with_mixed_column_naming,
        table="public.target_table",
        # TODO: после фикса бага https://jira.mts.ru/browse/DOP-8666 в onetl, пофиксить тесты
        columns=list(map(lambda x: f'"{x}"'.lower(), init_df_with_mixed_column_naming.columns)),
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    for field in init_df_with_mixed_column_naming.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.collect() == init_df_with_mixed_column_naming.collect()


async def test_change_mixed_column_naming_to_hive_default_case(
    client: AsyncClient,
    transfers_with_mixed_column_naming,
    prepare_hive_with_mixed_column_naming,
    init_df_with_mixed_column_naming: DataFrame,
    spark,
):
    # Arrange
    user: MockUser = transfers_with_mixed_column_naming["group_owner"]
    transfer: Transfer = transfers_with_mixed_column_naming["postgres_hive"]

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": transfer.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=user.token,
    )
    assert run_data["status"] == Status.FINISHED.value
    reader = DBReader(
        connection=prepare_hive_with_mixed_column_naming,
        table="public.target_table",
        # TODO: после фикса бага https://jira.mts.ru/browse/DOP-8666 в onetl, пофиксить тесты
        columns=[f"`{column.lower()}`" for column in init_df_with_mixed_column_naming.columns],
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    for field in init_df_with_mixed_column_naming.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.collect() == init_df_with_mixed_column_naming.collect()
