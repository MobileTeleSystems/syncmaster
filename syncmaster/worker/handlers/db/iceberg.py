# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.connection import Iceberg
from onetl.hooks import slot, support_hooks

from syncmaster.dto.connections import (
    IcebergRESTCatalogBasicAuthS3BasicDTO,
    IcebergRESTCatalogBasicAuthS3DelegatedDTO,
    IcebergRESTCatalogOAuth2ClientCredentialsS3BasicDTO,
    IcebergRESTCatalogOAuth2ClientCredentialsS3DelegatedDTO,
    IcebergRESTCatalogS3DelegatedConnectionBaseDTO,
    IcebergRESTCatalogS3DirectConnectionBaseDTO,
)
from syncmaster.dto.transfers import IcebergTransferDTO
from syncmaster.worker.handlers.db.base import DBHandler

if TYPE_CHECKING:
    from pyspark.sql import SparkSession
    from pyspark.sql.dataframe import DataFrame


@support_hooks
class IcebergRESTCatalogS3Handler(DBHandler):
    connection: Iceberg
    connection_dto: IcebergRESTCatalogS3DirectConnectionBaseDTO | IcebergRESTCatalogS3DelegatedConnectionBaseDTO
    transfer_dto: IcebergTransferDTO
    _operators = {
        "regexp": "RLIKE",
        **DBHandler._operators,
    }

    def connect(self, spark: SparkSession):
        if isinstance(self.connection_dto, IcebergRESTCatalogS3DirectConnectionBaseDTO):
            self.connection = Iceberg(
                spark=spark,
                catalog_name=self.transfer_dto.catalog_name,
                catalog=Iceberg.RESTCatalog(
                    url=self.connection_dto.rest_catalog_url,
                    auth=self._make_auth(),
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
        else:
            self.connection = Iceberg(
                spark=spark,
                catalog_name=self.transfer_dto.catalog_name,
                catalog=Iceberg.RESTCatalog(
                    url=self.connection_dto.rest_catalog_url,
                    auth=self._make_auth(),
                ),
                warehouse=Iceberg.DelegatedWarehouse(
                    name=self.connection_dto.s3_warehouse_name,
                    access_delegation=self.connection_dto.s3_access_delegation,
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

    def _make_auth(self):
        if isinstance(
            self.connection_dto,
            IcebergRESTCatalogOAuth2ClientCredentialsS3BasicDTO
            | IcebergRESTCatalogOAuth2ClientCredentialsS3DelegatedDTO,
        ):
            return Iceberg.RESTCatalog.OAuth2ClientCredentials(
                client_id=self.connection_dto.rest_catalog_oauth2_client_id,
                client_secret=self.connection_dto.rest_catalog_oauth2_client_secret,
                scopes=self.connection_dto.rest_catalog_oauth2_scopes,
                resource=self.connection_dto.rest_catalog_oauth2_resource,
                audience=self.connection_dto.rest_catalog_oauth2_audience,
                oauth2_token_endpoint=self.connection_dto.rest_catalog_oauth2_token_endpoint,
            )
        if isinstance(
            self.connection_dto,
            IcebergRESTCatalogBasicAuthS3DelegatedDTO | IcebergRESTCatalogBasicAuthS3BasicDTO,
        ):
            return Iceberg.RESTCatalog.BasicAuth(
                user=self.connection_dto.rest_catalog_username,
                password=self.connection_dto.rest_catalog_password,
            )
        return None
