import secrets

import pytest
import pytest_asyncio
from httpx import AsyncClient
from onetl.connection import MySQL
from onetl.db import DBReader
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, from_unixtime
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Group, Queue, Status, Transfer
from tests.mocks import MockUser
from tests.test_unit.utils import create_transfer
from tests.utils import get_run_on_end

pytestmark = [pytest.mark.asyncio, pytest.mark.worker]


@pytest_asyncio.fixture
async def postgres_to_mysql(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    mysql_for_conftest: MySQL,
    mysql_connection: Connection,
    postgres_connection: Connection,
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
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


async def test_run_transfer_postgres_to_mysql(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_mysql,
    init_df: DataFrame,
    postgres_to_mysql: Transfer,
):
    # Arrange
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df)
    mysql, _ = prepare_mysql

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": postgres_to_mysql.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=group_owner.token,
    )
    source_auth_data = run_data["transfer_dump"]["source_connection"]["auth_data"]
    target_auth_data = run_data["transfer_dump"]["target_connection"]["auth_data"]

    assert run_data["status"] == Status.FINISHED.value
    assert source_auth_data["user"]
    assert "password" not in source_auth_data
    assert target_auth_data["user"]
    assert "password" not in target_auth_data
    reader = DBReader(
        connection=mysql,
        table=f"{mysql.database}.target_table",
    )
    df = reader.run()

    # as spark rounds milliseconds to seconds while writing to mysql: https://onetl.readthedocs.io/en/latest/connection/db_connection/mysql/types.html#id5
    df = df.withColumn(
        "REGISTERED_AT",
        from_unixtime((col("REGISTERED_AT").cast("double") + 0.5).cast("long")).cast("timestamp"),
    )
    init_df = init_df.withColumn(
        "REGISTERED_AT",
        from_unixtime((col("REGISTERED_AT").cast("double") + 0.5).cast("long")).cast("timestamp"),
    )
    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("ID").collect() == init_df.sort("ID").collect()


async def test_run_transfer_postgres_to_mysql_mixed_naming(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_postgres,
    prepare_mysql,
    init_df_with_mixed_column_naming: DataFrame,
    postgres_to_mysql: Transfer,
):
    # Arrange
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df_with_mixed_column_naming)
    mysql, _ = prepare_mysql

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": postgres_to_mysql.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=group_owner.token,
    )
    source_auth_data = run_data["transfer_dump"]["source_connection"]["auth_data"]
    target_auth_data = run_data["transfer_dump"]["target_connection"]["auth_data"]

    assert run_data["status"] == Status.FINISHED.value
    assert source_auth_data["user"]
    assert "password" not in source_auth_data
    assert target_auth_data["user"]
    assert "password" not in target_auth_data

    reader = DBReader(
        connection=mysql,
        table=f"{mysql.database}.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    # as spark rounds milliseconds to seconds while writing to mysql: https://onetl.readthedocs.io/en/latest/connection/db_connection/mysql/types.html#id5
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

    assert df.collect() == init_df_with_mixed_column_naming.collect()


async def test_run_transfer_mysql_to_postgres(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_mysql,
    prepare_postgres,
    init_df: DataFrame,
    mysql_to_postgres: Transfer,
):
    # Arrange
    _, fill_with_data = prepare_mysql
    fill_with_data(init_df)
    postgres, _ = prepare_postgres

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": mysql_to_postgres.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=group_owner.token,
    )
    source_auth_data = run_data["transfer_dump"]["source_connection"]["auth_data"]
    target_auth_data = run_data["transfer_dump"]["target_connection"]["auth_data"]

    assert run_data["status"] == Status.FINISHED.value
    assert source_auth_data["user"]
    assert "password" not in source_auth_data
    assert target_auth_data["user"]
    assert "password" not in target_auth_data

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    # as spark rounds milliseconds to seconds while writing to mysql: https://onetl.readthedocs.io/en/latest/connection/db_connection/mysql/types.html#id5
    df = df.withColumn(
        "REGISTERED_AT",
        from_unixtime((col("REGISTERED_AT").cast("double") + 0.5).cast("long")).cast("timestamp"),
    )
    init_df = init_df.withColumn(
        "REGISTERED_AT",
        from_unixtime((col("REGISTERED_AT").cast("double") + 0.5).cast("long")).cast("timestamp"),
    )
    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("ID").collect() == init_df.sort("ID").collect()


async def test_run_transfer_mysql_to_postgres_mixed_naming(
    client: AsyncClient,
    group_owner: MockUser,
    prepare_mysql,
    prepare_postgres,
    init_df_with_mixed_column_naming: DataFrame,
    mysql_to_postgres: Transfer,
):
    # Arrange
    _, fill_with_data = prepare_mysql
    fill_with_data(init_df_with_mixed_column_naming)
    postgres, _ = prepare_postgres

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": mysql_to_postgres.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=group_owner.token,
    )
    source_auth_data = run_data["transfer_dump"]["source_connection"]["auth_data"]
    target_auth_data = run_data["transfer_dump"]["target_connection"]["auth_data"]

    assert run_data["status"] == Status.FINISHED.value
    assert source_auth_data["user"]
    assert "password" not in source_auth_data
    assert target_auth_data["user"]
    assert "password" not in target_auth_data

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()

    assert df.columns != init_df_with_mixed_column_naming.columns
    assert df.columns == [column.lower() for column in init_df_with_mixed_column_naming.columns]

    # as spark rounds milliseconds to seconds while writing to mysql: https://onetl.readthedocs.io/en/latest/connection/db_connection/mysql/types.html#id5
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

    assert df.collect() == init_df_with_mixed_column_naming.collect()
