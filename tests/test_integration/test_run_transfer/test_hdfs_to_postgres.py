import pytest
from httpx import AsyncClient
from onetl.db import DBReader
from pyspark.sql import DataFrame

from syncmaster.db.models import Status, Transfer
from tests.mocks import MockUser
from tests.test_integration.test_run_transfer.conftest import df_schema
from tests.utils import get_run_on_end

pytestmark = [pytest.mark.asyncio, pytest.mark.worker, pytest.mark.hdfs, pytest.mark.postgres]


@pytest.mark.parametrize("choice_file_type", ["with_header"], indirect=True)
@pytest.mark.parametrize("choice_file_format", ["csv"], indirect=True)
async def test_run_hdfs_transfer_csv(
    choice_file_format,
    choice_file_type,
    prepare_postgres,
    prepare_hdfs,
    transfers: dict[str, MockUser | Transfer],
    init_df: DataFrame,
    client: AsyncClient,
    spark,
):
    # Arrange
    user: MockUser = transfers["group_owner"]
    transfer: Transfer = transfers["hdfs_postgres"]

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
        connection=prepare_postgres,
        table="public.target_table",
    )
    df = reader.run()
    for field in df_schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("id").collect() == init_df.sort("id").collect()


@pytest.mark.parametrize("choice_file_type", ["without_compression"], indirect=True)
@pytest.mark.parametrize("choice_file_format", ["jsonline"], indirect=True)
async def test_run_hdfs_transfer_jsonline(
    choice_file_format,
    choice_file_type,
    prepare_postgres,
    prepare_hdfs,
    transfers: dict[str, MockUser | Transfer],
    init_df: DataFrame,
    client: AsyncClient,
    spark,
):
    # Arrange
    user: MockUser = transfers["group_owner"]
    transfer: Transfer = transfers["hdfs_postgres"]

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
        connection=prepare_postgres,
        table="public.target_table",
    )
    df = reader.run()
    for field in df_schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("id").collect() == init_df.sort("id").collect()


@pytest.mark.parametrize("choice_file_type", ["without_compression"], indirect=True)
@pytest.mark.parametrize("choice_file_format", ["json"], indirect=True)
async def test_run_hdfs_transfer_json(
    choice_file_format,
    choice_file_type,
    prepare_postgres,
    prepare_hdfs,
    transfers: dict[str, MockUser | Transfer],
    init_df: DataFrame,
    client: AsyncClient,
    spark,
):
    # Arrange
    user: MockUser = transfers["group_owner"]
    transfer: Transfer = transfers["hdfs_postgres"]

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
        connection=prepare_postgres,
        table="public.target_table",
    )
    df = reader.run()
    for field in df_schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("ID").collect() == init_df.sort("ID").collect()
