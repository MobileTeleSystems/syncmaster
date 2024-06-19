import secrets

import pytest
import pytest_asyncio
from httpx import AsyncClient
from onetl.db import DBReader
from pyspark.sql import DataFrame
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Group, Queue, Status, Transfer
from tests.mocks import MockUser
from tests.test_unit.utils import create_transfer
from tests.utils import get_run_on_end

pytestmark = [pytest.mark.asyncio, pytest.mark.worker]


@pytest_asyncio.fixture
async def postgres_to_hive(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    hive_connection: Connection,
    postgres_connection: Connection,
):
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"postgres2hive_{secrets.token_hex(5)}",
        source_connection_id=postgres_connection.id,
        target_connection_id=hive_connection.id,
        source_params={
            "type": "postgres",
            "table_name": "public.source_table",
        },
        target_params={
            "type": "hive",
            "table_name": "default.target_table",
        },
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest_asyncio.fixture
async def hive_to_postgres(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    hive_connection: Connection,
    postgres_connection: Connection,
):
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"hive2postgres_{secrets.token_hex(5)}",
        source_connection_id=hive_connection.id,
        target_connection_id=postgres_connection.id,
        source_params={
            "type": "hive",
            "table_name": "default.source_table",
        },
        target_params={
            "type": "postgres",
            "table_name": "public.target_table",
        },
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


async def test_run_transfer_postgres_to_hive(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_hive,
    init_df: DataFrame,
    postgres_to_hive: Transfer,
):
    # Arrange
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df)
    hive, _ = prepare_hive

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": postgres_to_hive.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=group_owner.token,
    )
    assert run_data["status"] == Status.FINISHED.value
    assert run_data["transfer_dump"]["source_connection"]["auth_data"]
    assert run_data["transfer_dump"]["target_connection"]["auth_data"]

    reader = DBReader(
        connection=hive,
        table="default.target_table",
    )
    df = reader.run()
    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("ID").collect() == init_df.sort("ID").collect()


async def test_run_transfer_postgres_to_hive_mixed_naming(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_hive,
    init_df_with_mixed_column_naming: DataFrame,
    postgres_to_hive: Transfer,
):
    # Arrange
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df_with_mixed_column_naming)
    hive, _ = prepare_hive

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": postgres_to_hive.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=group_owner.token,
    )
    assert run_data["status"] == Status.FINISHED.value
    assert run_data["transfer_dump"]["source_connection"]["auth_data"]
    assert run_data["transfer_dump"]["target_connection"]["auth_data"]
    reader = DBReader(
        connection=hive,
        table="default.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    for field in init_df_with_mixed_column_naming.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.collect() == init_df_with_mixed_column_naming.collect()


async def test_run_transfer_hive_to_postgres(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_hive,
    prepare_postgres,
    init_df: DataFrame,
    hive_to_postgres: Transfer,
):
    # Arrange
    _, fill_with_data = prepare_hive
    fill_with_data(init_df)
    postgres, _ = prepare_postgres

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": hive_to_postgres.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=group_owner.token,
    )
    assert run_data["status"] == Status.FINISHED.value
    assert run_data["transfer_dump"]["source_connection"]["auth_data"]
    assert run_data["transfer_dump"]["target_connection"]["auth_data"]
    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()
    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("ID").collect() == init_df.sort("ID").collect()


async def test_run_transfer_hive_to_postgres_mixes_naming(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_hive,
    prepare_postgres,
    init_df_with_mixed_column_naming: DataFrame,
    hive_to_postgres: Transfer,
):
    # Arrange
    _, fill_with_data = prepare_hive
    fill_with_data(init_df_with_mixed_column_naming)
    postgres, _ = prepare_postgres

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": hive_to_postgres.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=group_owner.token,
    )
    assert run_data["status"] == Status.FINISHED.value
    assert run_data["transfer_dump"]["source_connection"]["auth_data"]
    assert run_data["transfer_dump"]["target_connection"]["auth_data"]

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    for field in init_df_with_mixed_column_naming.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.collect() == init_df_with_mixed_column_naming.collect()
