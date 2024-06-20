import os
import secrets

import pytest
import pytest_asyncio
from httpx import AsyncClient
from onetl.connection import SparkHDFS
from onetl.db import DBReader
from onetl.file import FileDFReader
from pyspark.sql import DataFrame
from pytest import FixtureRequest
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Group, Queue, Status
from tests.mocks import MockUser
from tests.test_unit.utils import create_transfer
from tests.utils import get_run_on_end

pytestmark = [pytest.mark.asyncio, pytest.mark.worker]


@pytest.fixture(params=[""])
def file_format_flavor(request: FixtureRequest):
    return request.param


@pytest_asyncio.fixture
async def hdfs_to_postgres(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    init_df: DataFrame,
    hdfs_connection: Connection,
    postgres_connection: Connection,
    prepare_hdfs,
    source_file_format,
    file_format_flavor: str,
):
    format_name, file_format = source_file_format
    _, source_path, _ = prepare_hdfs

    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"hdfs2postgres_{secrets.token_hex(5)}",
        source_connection_id=hdfs_connection.id,
        target_connection_id=postgres_connection.id,
        source_params={
            "type": "hdfs",
            "directory_path": os.fspath(source_path / "file_df_connection" / format_name / file_format_flavor),
            "file_format": {
                "type": format_name,
                **file_format.dict(),
            },
            "df_schema": init_df.schema.json(),
            "options": {},
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


@pytest_asyncio.fixture(params=[""])
async def postgres_to_hdfs(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    hdfs_connection: Connection,
    postgres_connection: Connection,
    target_file_format,
    file_format_flavor: str,
):
    format_name, file_format = target_file_format
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"postgres2hdfs_{secrets.token_hex(5)}",
        source_connection_id=postgres_connection.id,
        target_connection_id=hdfs_connection.id,
        source_params={
            "type": "postgres",
            "table_name": "public.source_table",
        },
        target_params={
            "type": "hdfs",
            "directory_path": f"/target/{format_name}/{file_format_flavor}",
            "file_format": {
                "type": format_name,
                **file_format.dict(),
            },
            "options": {},
        },
        queue_id=queue.id,
    )
    yield result
    await session.delete(result)
    await session.commit()


@pytest.mark.parametrize(
    "source_file_format, file_format_flavor",
    [
        pytest.param(
            ("csv", {}),
            "with_header",
            id="csv",
        ),
        pytest.param(
            ("json", {}),
            "without_compression",
            id="json",
        ),
        pytest.param(
            ("jsonline", {}),
            "without_compression",
            id="jsonline",
        ),
    ],
    indirect=["source_file_format", "file_format_flavor"],
)
async def test_run_transfer_hdfs_to_postgres(
    prepare_postgres,
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    hdfs_to_postgres: Connection,
    source_file_format,
    file_format_flavor,
):
    # Arrange
    postgres, _ = prepare_postgres

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": hdfs_to_postgres.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=group_owner.token,
    )
    assert run_data["status"] == Status.FINISHED.value
    assert run_data["transfer_dump"]["source_connection"]["auth_data"]["user"]
    assert not run_data["transfer_dump"]["source_connection"]["auth_data"].get("password", None)
    assert run_data["transfer_dump"]["target_connection"]["auth_data"]["user"]
    assert not run_data["transfer_dump"]["target_connection"]["auth_data"].get("password", None)

    reader = DBReader(
        connection=postgres,
        table="public.target_table",
    )
    df = reader.run()
    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("id").collect() == init_df.sort("id").collect()


@pytest.mark.parametrize(
    "target_file_format, file_format_flavor",
    [
        pytest.param(
            ("csv", {}),
            "with_header",
            id="csv",
        ),
        pytest.param(
            ("jsonline", {}),
            "without_compression",
            id="jsonline",
        ),
    ],
    indirect=["target_file_format", "file_format_flavor"],
)
async def test_run_transfer_postgres_to_hdfs(
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    prepare_postgres,
    hdfs_file_df_connection: SparkHDFS,
    postgres_to_hdfs: Connection,
    hdfs_connection: SparkHDFS,
    target_file_format,
    file_format_flavor: str,
):
    format_name, format = target_file_format

    # Arrange
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df)

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": postgres_to_hdfs.id},
    )
    # Assert
    assert result.status_code == 200

    run_data = await get_run_on_end(
        client=client,
        run_id=result.json()["id"],
        token=group_owner.token,
    )
    assert run_data["status"] == Status.FINISHED.value
    assert run_data["transfer_dump"]["source_connection"]["auth_data"]["user"]
    assert not run_data["transfer_dump"]["source_connection"]["auth_data"].get("password", None)
    assert run_data["transfer_dump"]["target_connection"]["auth_data"]["user"]
    assert not run_data["transfer_dump"]["target_connection"]["auth_data"].get("password", None)

    reader = FileDFReader(
        connection=hdfs_file_df_connection,
        format=format,
        source_path=f"/target/{format_name}/{file_format_flavor}",
        df_schema=init_df.schema,
        options={},
    )
    df = reader.run()

    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("id").collect() == init_df.sort("id").collect()
