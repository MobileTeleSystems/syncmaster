import pytest
from httpx import AsyncClient
from onetl.db import DBReader
from pyspark.sql import DataFrame
from tests.utils import MockUser, get_run_on_end

from app.db.models import Status, Transfer

pytestmark = [pytest.mark.asyncio]


async def test_run_simple_transfer(
    client: AsyncClient,
    transfers: dict[str, MockUser | Transfer],
    prepare_postgres,
    init_df: DataFrame,
):
    # Arrange
    user: MockUser = transfers["group_owner"]
    transfer: Transfer = transfers["hive_postgres"]

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
        columns=list(map(lambda x: f'"{x}"'.lower(), init_df.columns)),
    )
    # TODO: после фикса бага https://jira.mts.ru/browse/DOP-8666 в onetl, пофиксить тесты
    df = reader.run()
    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("ID").collect() == init_df.sort("ID").collect()
