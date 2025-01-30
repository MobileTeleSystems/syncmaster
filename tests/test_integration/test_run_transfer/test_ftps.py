import os
import secrets
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import AsyncClient
from onetl.connection import FTPS, SparkLocalFS
from onetl.db import DBReader
from onetl.file import FileDFReader, FileDownloader
from pyspark.sql import DataFrame
from pyspark.sql.functions import col, date_format, date_trunc, to_timestamp
from pytest import FixtureRequest
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Connection, Group, Queue, Status
from syncmaster.db.models.transfer import Transfer
from tests.mocks import MockUser
from tests.test_unit.utils import create_transfer
from tests.utils import get_run_on_end

pytestmark = [pytest.mark.asyncio, pytest.mark.worker]


@pytest.fixture(params=[""])
def file_format_flavor(request: FixtureRequest):
    return request.param


@pytest_asyncio.fixture
async def ftps_to_postgres(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    init_df: DataFrame,
    ftps_connection: Connection,
    postgres_connection: Connection,
    prepare_ftps,
    source_file_format,
    file_format_flavor: str,
):
    format_name, file_format = source_file_format
    format_name_in_path = "xlsx" if format_name == "excel" else format_name
    _, source_path, _ = prepare_ftps

    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"ftps2postgres_{secrets.token_hex(5)}",
        source_connection_id=ftps_connection.id,
        target_connection_id=postgres_connection.id,
        source_params={
            "type": "ftps",
            "directory_path": os.fspath(source_path / "file_df_connection" / format_name_in_path / file_format_flavor),
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
async def postgres_to_ftps(
    session: AsyncSession,
    group: Group,
    queue: Queue,
    ftps_connection: Connection,
    postgres_connection: Connection,
    target_file_format,
    file_format_flavor: str,
):
    format_name, file_format = target_file_format
    result = await create_transfer(
        session=session,
        group_id=group.id,
        name=f"postgres2ftps_{secrets.token_hex(5)}",
        source_connection_id=postgres_connection.id,
        target_connection_id=ftps_connection.id,
        source_params={
            "type": "postgres",
            "table_name": "public.source_table",
        },
        target_params={
            "type": "ftps",
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
        pytest.param(
            ("excel", {}),
            "with_header",
            id="excel",
        ),
        pytest.param(
            ("orc", {}),
            "without_compression",
            id="orc",
        ),
        pytest.param(
            ("parquet", {}),
            "without_compression",
            id="parquet",
        ),
        pytest.param(
            ("xml", {}),
            "without_compression",
            id="xml",
        ),
    ],
    indirect=["source_file_format", "file_format_flavor"],
)
async def test_run_transfer_ftps_to_postgres(
    prepare_postgres,
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    ftps_to_postgres: Transfer,
    source_file_format,
    file_format_flavor,
):
    # Arrange
    postgres, _ = prepare_postgres
    file_format, _ = source_file_format

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": ftps_to_postgres.id},
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

    # as Excel does not support datetime values with precision greater than milliseconds
    if file_format == "excel":
        df = df.withColumn("REGISTERED_AT", date_trunc("second", col("REGISTERED_AT")))
        init_df = init_df.withColumn("REGISTERED_AT", date_trunc("second", col("REGISTERED_AT")))

    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("id").collect() == init_df.sort("id").collect()


@pytest.mark.parametrize(
    "target_file_format, file_format_flavor",
    [
        pytest.param(
            ("csv", {"compression": "lz4"}),
            "with_compression",
            id="csv",
        ),
        pytest.param(
            ("jsonline", {}),
            "without_compression",
            id="jsonline",
        ),
        pytest.param(
            ("excel", {}),
            "with_header",
            id="excel",
        ),
        pytest.param(
            ("orc", {"compression": "snappy"}),
            "with_compression",
            id="orc",
        ),
        pytest.param(
            ("parquet", {"compression": "lz4"}),
            "with_compression",
            id="parquet",
        ),
        pytest.param(
            ("xml", {"compression": "snappy"}),
            "with_compression",
            id="xml",
        ),
    ],
    indirect=["target_file_format", "file_format_flavor"],
)
async def test_run_transfer_postgres_to_ftps(
    group_owner: MockUser,
    init_df: DataFrame,
    client: AsyncClient,
    prepare_postgres,
    ftps_file_connection: FTPS,
    ftps_file_df_connection: SparkLocalFS,
    postgres_to_ftps: Transfer,
    target_file_format,
    file_format_flavor: str,
    tmp_path: Path,
):
    format_name, format = target_file_format

    # Arrange
    _, fill_with_data = prepare_postgres
    fill_with_data(init_df)

    # Act
    result = await client.post(
        "v1/runs",
        headers={"Authorization": f"Bearer {group_owner.token}"},
        json={"transfer_id": postgres_to_ftps.id},
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

    downloader = FileDownloader(
        connection=ftps_file_connection,
        source_path=f"/target/{format_name}/{file_format_flavor}",
        local_path=tmp_path,
    )
    downloader.run()

    reader = FileDFReader(
        connection=ftps_file_df_connection,
        format=format,
        source_path=tmp_path,
        df_schema=init_df.schema,
    )
    df = reader.run()

    # as Excel does not support datetime values with precision greater than milliseconds
    if format_name == "excel":
        init_df = init_df.withColumn(
            "REGISTERED_AT",
            to_timestamp(date_format(col("REGISTERED_AT"), "yyyy-MM-dd HH:mm:ss.SSS")),
        )

    for field in init_df.schema:
        df = df.withColumn(field.name, df[field.name].cast(field.dataType))

    assert df.sort("id").collect() == init_df.sort("id").collect()
