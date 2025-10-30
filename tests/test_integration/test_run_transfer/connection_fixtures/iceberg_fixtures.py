import logging
import secrets

import pytest
import pytest_asyncio
from onetl.connection import S3, Iceberg
from onetl.db import DBWriter
from pyspark.sql import DataFrame, SparkSession
from sqlalchemy.ext.asyncio import AsyncSession

from syncmaster.db.models import Group
from syncmaster.dto.connections import IcebergRESTCatalogS3ConnectionDTO
from syncmaster.server.settings import ServerAppSettings as Settings
from tests.settings import TestSettings
from tests.test_unit.utils import create_connection, create_credentials

logger = logging.getLogger(__name__)


@pytest.fixture(
    scope="session",
    params=[pytest.param("iceberg", marks=[pytest.mark.iceberg])],
)
def iceberg_rest_s3_for_conftest(test_settings: TestSettings) -> IcebergRESTCatalogS3ConnectionDTO:
    return IcebergRESTCatalogS3ConnectionDTO(
        metastore_url=test_settings.TEST_ICEBERG_METASTORE_URL_FOR_CONFTEST,
        s3_warehouse_path=test_settings.TEST_ICEBERG_S3_WAREHOUSE_PATH,
        s3_host=test_settings.TEST_S3_HOST_FOR_CONFTEST,
        s3_port=test_settings.TEST_S3_PORT_FOR_CONFTEST,
        s3_protocol=test_settings.TEST_S3_PROTOCOL,
        s3_bucket=test_settings.TEST_S3_BUCKET,
        s3_region=test_settings.TEST_ICEBERG_S3_REGION,
        s3_path_style_access=test_settings.TEST_ICEBERG_S3_PATH_STYLE_ACCESS,
        s3_access_key=test_settings.TEST_S3_ACCESS_KEY,
        s3_secret_key=test_settings.TEST_S3_SECRET_KEY,
        metastore_username=test_settings.TEST_ICEBERG_METASTORE_USERNAME,
        metastore_password=test_settings.TEST_ICEBERG_METASTORE_PASSWORD,
    )


@pytest.fixture(
    scope="session",
    params=[pytest.param("iceberg", marks=[pytest.mark.iceberg])],
)
def iceberg_rest_s3_for_worker(test_settings: TestSettings) -> IcebergRESTCatalogS3ConnectionDTO:
    return IcebergRESTCatalogS3ConnectionDTO(
        metastore_url=test_settings.TEST_ICEBERG_METASTORE_URL_FOR_WORKER,
        s3_warehouse_path=test_settings.TEST_ICEBERG_S3_WAREHOUSE_PATH,
        s3_host=test_settings.TEST_S3_HOST_FOR_WORKER,
        s3_port=test_settings.TEST_S3_PORT_FOR_WORKER,
        s3_protocol=test_settings.TEST_S3_PROTOCOL,
        s3_bucket=test_settings.TEST_S3_BUCKET,
        s3_region=test_settings.TEST_ICEBERG_S3_REGION,
        s3_path_style_access=test_settings.TEST_ICEBERG_S3_PATH_STYLE_ACCESS,
        s3_access_key=test_settings.TEST_S3_ACCESS_KEY,
        s3_secret_key=test_settings.TEST_S3_SECRET_KEY,
        metastore_username=test_settings.TEST_ICEBERG_METASTORE_USERNAME,
        metastore_password=test_settings.TEST_ICEBERG_METASTORE_PASSWORD,
    )


@pytest.fixture
def prepare_iceberg_rest_s3(
    spark: SparkSession,
    iceberg_rest_s3_for_conftest: IcebergRESTCatalogS3ConnectionDTO,
    s3_file_connection: S3,
):
    iceberg = iceberg_rest_s3_for_conftest
    catalog_name = "iceberg_rest_s3"
    namespace = "default"
    source_table = f"{catalog_name}.{namespace}.source_table"
    target_table = f"{catalog_name}.{namespace}.target_table"

    connection = Iceberg(
        spark=spark,
        catalog_name=catalog_name,
        catalog=Iceberg.RESTCatalog(
            uri=iceberg.metastore_url,
            auth=Iceberg.RESTCatalog.BasicAuth(
                user=iceberg.metastore_username,
                password=iceberg.metastore_password,
            ),
        ),
        warehouse=Iceberg.S3Warehouse(
            path=iceberg.s3_warehouse_path,
            host=iceberg.s3_host,
            port=iceberg.s3_port,
            protocol=iceberg.s3_protocol,
            bucket=iceberg.s3_bucket,
            path_style_access=iceberg.s3_path_style_access,
            region=iceberg.s3_region,
            access_key=iceberg.s3_access_key,
            secret_key=iceberg.s3_secret_key,
        ),
    ).check()

    connection.execute(f"DROP TABLE IF EXISTS {source_table}")
    connection.execute(f"DROP TABLE IF EXISTS {target_table}")
    connection.execute(f"CREATE NAMESPACE IF NOT EXISTS {catalog_name}.{namespace}")

    def fill_with_data(df: DataFrame):
        logger.info("START PREPARE ICEBERG")
        db_writer = DBWriter(
            connection=connection,
            target=f"{namespace}.source_table",
        )
        db_writer.run(df)
        spark.catalog.refreshTable(source_table)
        logger.info("END PREPARE ICEBERG")

    yield connection, fill_with_data

    connection.execute(f"DROP TABLE IF EXISTS {source_table}")
    connection.execute(f"DROP TABLE IF EXISTS {target_table}")


@pytest_asyncio.fixture
async def iceberg_rest_s3_connection(
    iceberg_rest_s3_for_worker: IcebergRESTCatalogS3ConnectionDTO,
    settings: Settings,
    session: AsyncSession,
    group: Group,
):
    iceberg = iceberg_rest_s3_for_worker
    result = await create_connection(
        session=session,
        name=secrets.token_hex(5),
        type=iceberg.type,
        data=dict(
            metastore_url=iceberg.metastore_url,
            s3_warehouse_path=iceberg.s3_warehouse_path,
            s3_host=iceberg.s3_host,
            s3_port=iceberg.s3_port,
            s3_protocol=iceberg.s3_protocol,
            s3_bucket=iceberg.s3_bucket,
            s3_region=iceberg.s3_region,
            s3_path_style_access=iceberg.s3_path_style_access,
        ),
        group_id=group.id,
    )

    await create_credentials(
        session=session,
        settings=settings,
        connection_id=result.id,
        auth_data=dict(
            type="iceberg_rest_basic_s3_basic",
            s3_access_key=iceberg.s3_access_key,
            s3_secret_key=iceberg.s3_secret_key,
            metastore_username=iceberg.metastore_username,
            metastore_password=iceberg.metastore_password,
        ),
    )

    yield result
    await session.delete(result)
    await session.commit()
