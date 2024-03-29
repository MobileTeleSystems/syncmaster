import pytest
from httpx import AsyncClient
from onetl.file import FileDFReader
from pyspark.sql import DataFrame

from syncmaster.db.models import Status, Transfer
from tests.mocks import MockUser
from tests.utils import get_run_on_end

pytestmark = [pytest.mark.asyncio, pytest.mark.worker, pytest.mark.hdfs, pytest.mark.postgres]


@pytest.mark.parametrize("choice_file_type", ["without_header"], indirect=True)
@pytest.mark.parametrize("choice_file_format", ["csv"], indirect=True)
async def test_run_pg_to_hdfs_transfer_csv(
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
    hdfs_file_format, file_object = choice_file_format
    hdfs_connection, _, _ = prepare_hdfs
    user: MockUser = transfers["group_owner"]
    transfer: Transfer = transfers["postgres_hdfs"]

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

    reader = FileDFReader(
        connection=hdfs_connection,
        format=file_object,
        source_path=f"/target/{hdfs_file_format}/{choice_file_type}",
        options={},
        df_schema=init_df.schema,
    )
    df = reader.run()

    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))
    assert df.sort("ID").collect() == init_df.sort("ID").collect()


@pytest.mark.parametrize("choice_file_type", ["without_compression"], indirect=True)
@pytest.mark.parametrize("choice_file_format", ["jsonline"], indirect=True)
async def test_run_pg_to_hdfs_transfer_jsonline(
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
    hdfs_file_format, file_object = choice_file_format
    hdfs_connection, _, _ = prepare_hdfs
    user: MockUser = transfers["group_owner"]
    transfer: Transfer = transfers["postgres_hdfs"]

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

    reader = FileDFReader(
        connection=hdfs_connection,
        format=file_object,
        source_path=f"/target/{hdfs_file_format}/{choice_file_type}",
        options={},
        df_schema=init_df.schema,
    )
    df = reader.run()

    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))
    assert df.sort("ID").collect() == init_df.sort("ID").collect()
