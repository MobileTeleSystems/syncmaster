import pytest
from httpx import AsyncClient
from onetl.file import FileDFReader
from pyspark.sql import DataFrame
from tests.utils import MockUser, get_run_on_end

from app.db.models import Status, Transfer

pytestmark = [pytest.mark.asyncio]


@pytest.mark.parametrize("choice_s3_file_type", ["without_header"], indirect=True)
@pytest.mark.parametrize("choice_s3_file_format", ["csv"], indirect=True)
async def test_run_pg_to_s3_transfer_csv(
    choice_s3_file_format,
    choice_s3_file_type,
    prepare_postgres,
    prepare_s3,
    transfers: dict[str, MockUser | Transfer],
    init_df: DataFrame,
    client: AsyncClient,
    spark,
):
    # Arrange
    s3_file_format, file_object = choice_s3_file_format
    s3_connection, _, _ = prepare_s3
    user: MockUser = transfers["group_owner"]  # type: ignore
    transfer: Transfer = transfers["postgres_s3"]  # type: ignore

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
        connection=s3_connection,
        format=file_object,
        source_path=f"/target/{s3_file_format}/{choice_s3_file_type}",
        options={},
        df_schema=init_df.schema,
    )
    # TODO: после фикса бага https://jira.mts.ru/browse/DOP-8666 в onetl, пофиксить тесты
    df = reader.run()

    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))
    assert df.sort("ID").collect() == init_df.sort("ID").collect()


@pytest.mark.parametrize("choice_s3_file_type", ["without_compression"], indirect=True)
@pytest.mark.parametrize("choice_s3_file_format", ["jsonline"], indirect=True)
async def test_run_pg_to_s3_transfer_jsonline(
    choice_s3_file_format,
    choice_s3_file_type,
    prepare_postgres,
    prepare_s3,
    transfers: dict[str, MockUser | Transfer],
    init_df: DataFrame,
    client: AsyncClient,
    spark,
):
    # Arrange
    s3_file_format, file_object = choice_s3_file_format
    s3_connection, _, _ = prepare_s3
    user: MockUser = transfers["group_owner"]  # type: ignore
    transfer: Transfer = transfers["postgres_s3"]  # type: ignore

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
        connection=s3_connection,
        format=file_object,
        source_path=f"/target/{s3_file_format}/{choice_s3_file_type}",
        options={},
        df_schema=init_df.schema,
    )
    # TODO: после фикса бага https://jira.mts.ru/browse/DOP-8666 в onetl, пофиксить тесты
    df = reader.run()

    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))
    assert df.sort("ID").collect() == init_df.sort("ID").collect()