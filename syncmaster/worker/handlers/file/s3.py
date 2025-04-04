# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0

from __future__ import annotations

from typing import TYPE_CHECKING

from onetl.file import FileDFReader

from syncmaster.dto.connections import S3ConnectionDTO
from syncmaster.worker.handlers.file.remote_df import RemoteDFFileHandler

if TYPE_CHECKING:
    from pyspark.sql import DataFrame, SparkSession


class S3Handler(RemoteDFFileHandler):
    connection_dto: S3ConnectionDTO

    def connect(self, spark: SparkSession):
        from onetl.connection import S3, SparkS3

        self.df_connection = SparkS3(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            access_key=self.connection_dto.access_key,
            secret_key=self.connection_dto.secret_key,
            bucket=self.connection_dto.bucket,
            protocol=self.connection_dto.protocol,
            region=self.connection_dto.region,
            extra=self.connection_dto.additional_params,
            spark=spark,
        ).check()

        self.file_connection = S3(
            host=self.connection_dto.host,
            port=self.connection_dto.port,
            access_key=self.connection_dto.access_key,
            secret_key=self.connection_dto.secret_key,
            bucket=self.connection_dto.bucket,
            protocol=self.connection_dto.protocol,
            region=self.connection_dto.region,
        ).check()

    def read(self) -> DataFrame:
        from pyspark.sql.types import StructType

        options = {}
        if self.transfer_dto.file_format.__class__.__name__ in ("Excel", "XML"):
            options = {"inferSchema": True}

        reader = FileDFReader(
            connection=self.df_connection,
            format=self.transfer_dto.file_format,
            source_path=self.transfer_dto.directory_path,
            df_schema=StructType.fromJson(self.transfer_dto.df_schema) if self.transfer_dto.df_schema else None,
            options={**options, **self.transfer_dto.options},
        )
        df = reader.run()

        rows_filter_expression = self._get_rows_filter_expression()
        if rows_filter_expression:
            df = df.where(rows_filter_expression)

        columns_filter_expressions = self._get_columns_filter_expressions()
        if columns_filter_expressions:
            df = df.selectExpr(*columns_filter_expressions)

        return df
