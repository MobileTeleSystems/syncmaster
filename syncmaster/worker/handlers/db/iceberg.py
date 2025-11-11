# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import Iceberg
from onetl.hooks import slot, support_hooks

from syncmaster.dto.connections import IcebergRESTCatalogS3ConnectionDTO
from syncmaster.dto.transfers import IcebergRESTCatalogS3TransferDTO
from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


@support_hooks
class IcebergRESTCatalogS3Handler(DBHandler):
    connection: Iceberg
    connection_dto: IcebergRESTCatalogS3ConnectionDTO
    transfer_dto: IcebergRESTCatalogS3TransferDTO
    _operators = {
        "regexp": "RLIKE",
        **DBHandler._operators,
    }

    def connect(self, spark: SparkSession):
        self.connection = Iceberg(
            spark=spark,
            catalog_name=self.transfer_dto.catalog_name,
            catalog=Iceberg.RESTCatalog(
                uri=self.connection_dto.metastore_url,
                auth=Iceberg.RESTCatalog.BasicAuth(
                    user=self.connection_dto.metastore_username,
                    password=self.connection_dto.metastore_password,
                ),
            ),
            warehouse=Iceberg.S3Warehouse(
                path=self.connection_dto.s3_warehouse_path,
                host=self.connection_dto.s3_host,
                port=self.connection_dto.s3_port,
                protocol=self.connection_dto.s3_protocol,
                bucket=self.connection_dto.s3_bucket,
                path_style_access=self.connection_dto.s3_bucket_style == "path",
                region=self.connection_dto.s3_region,
                access_key=self.connection_dto.s3_access_key,
                secret_key=self.connection_dto.s3_secret_key,
            ),
        ).check()

    @slot
    def read(self) -> DataFrame:
        table = ".".join([self.transfer_dto.catalog_name, self.transfer_dto.table_name])
        self.connection.spark.catalog.refreshTable(table)
        return super().read()

    @slot
    def write(self, df: DataFrame) -> None:
        return super().write(df)

    def _normalize_column_names(self, df: DataFrame) -> DataFrame:
        for column_name in df.columns:
            df = df.withColumnRenamed(column_name, column_name.lower())
        return df

    def _make_rows_filter_expression(self, filters: list[dict]) -> str | None:
        expressions = []
        for filter in filters:
            op = self._operators[filter["type"]]
            field = self._quote_field(filter["field"])
            value = filter.get("value")

            if value is None:
                expressions.append(f"{field} {op}")
                continue

            if op == "ILIKE":
                expressions.append(f"LOWER({field}) LIKE LOWER('{value}')")
            elif op == "NOT ILIKE":
                expressions.append(f"NOT LOWER({field}) LIKE LOWER('{value}')")
            else:
                expressions.append(f"{field} {op} '{value}'")

        return " AND ".join(expressions) or None

    def _get_reading_options(self) -> dict:
        return {}

    def _quote_field(self, field: str) -> str:
        return f"`{field}`"
