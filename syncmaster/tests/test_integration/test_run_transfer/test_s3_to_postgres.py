import pytest
from httpx import AsyncClient
from onetl.db import DBReader
from pyspark.sql import DataFrame
from tests.resources.file_df_connection.generate_files import get_data
from tests.test_integration.test_run_transfer.conftest import df_schema
from tests.utils import MockUser, get_run_on_end

from app.db.models import Status, Transfer

pytestmark = [pytest.mark.asyncio]


async def test_run_s3_transfer(
    client: AsyncClient,
    transfers: dict[str, MockUser | Transfer],
    prepare_s3,
    init_df: DataFrame,
    prepare_postgres,
    spark,
):
    # Arrange

    user: MockUser = transfers["group_owner"]  # type: ignore
    transfer: Transfer = transfers["s3_postgres"]  # type: ignore

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {user.token}"},
        json={"transfer_id": transfer.id},
    )
    # Assert
    df_reference = spark.createDataFrame(get_data(), df_schema)
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
    # TODO: после фикса бага https://jira.mts.ru/browse/DOP-8666 в onetl, пофиксить тесты
    df = reader.run()
    for field in df_schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("id").collect() == df_reference.sort("id").collect()
