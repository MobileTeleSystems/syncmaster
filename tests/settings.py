# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from pydantic import model_validator
from pydantic_settings import BaseSettings


class TestSettings(BaseSettings):
    TEST_POSTGRES_HOST_FOR_CONFTEST: str
    TEST_POSTGRES_PORT_FOR_CONFTEST: int
    TEST_POSTGRES_HOST_FOR_WORKER: str
    TEST_POSTGRES_PORT_FOR_WORKER: int
    TEST_POSTGRES_DB: str
    TEST_POSTGRES_USER: str
    TEST_POSTGRES_PASSWORD: str

    TEST_ORACLE_HOST_FOR_CONFTEST: str
    TEST_ORACLE_PORT_FOR_CONFTEST: int
    TEST_ORACLE_HOST_FOR_WORKER: str
    TEST_ORACLE_PORT_FOR_WORKER: int
    TEST_ORACLE_USER: str
    TEST_ORACLE_PASSWORD: str
    TEST_ORACLE_SID: str | None = None
    TEST_ORACLE_SERVICE_NAME: str | None = None

    TEST_CLICKHOUSE_HOST_FOR_CONFTEST: str
    TEST_CLICKHOUSE_PORT_FOR_CONFTEST: int
    TEST_CLICKHOUSE_HOST_FOR_WORKER: str
    TEST_CLICKHOUSE_PORT_FOR_WORKER: int
    TEST_CLICKHOUSE_USER: str
    TEST_CLICKHOUSE_PASSWORD: str
    TEST_CLICKHOUSE_DB: str

    TEST_MSSQL_HOST_FOR_CONFTEST: str
    TEST_MSSQL_PORT_FOR_CONFTEST: int
    TEST_MSSQL_HOST_FOR_WORKER: str
    TEST_MSSQL_PORT_FOR_WORKER: int
    TEST_MSSQL_USER: str
    TEST_MSSQL_PASSWORD: str
    TEST_MSSQL_DB: str

    TEST_MYSQL_HOST_FOR_CONFTEST: str
    TEST_MYSQL_PORT_FOR_CONFTEST: int
    TEST_MYSQL_HOST_FOR_WORKER: str
    TEST_MYSQL_PORT_FOR_WORKER: int
    TEST_MYSQL_USER: str
    TEST_MYSQL_PASSWORD: str
    TEST_MYSQL_DB: str

    TEST_HIVE_CLUSTER: str
    TEST_HIVE_USER: str
    TEST_HIVE_PASSWORD: str

    TEST_HDFS_HOST: str
    TEST_HDFS_WEBHDFS_PORT: int
    TEST_HDFS_IPC_PORT: int

    TEST_S3_HOST_FOR_CONFTEST: str
    TEST_S3_PORT_FOR_CONFTEST: int
    TEST_S3_HOST_FOR_WORKER: str
    TEST_S3_PORT_FOR_WORKER: int
    TEST_S3_BUCKET: str
    TEST_S3_ACCESS_KEY: str
    TEST_S3_SECRET_KEY: str
    TEST_S3_PROTOCOL: str = "http"
    TEST_S3_ADDITIONAL_PARAMS: dict = {}

    @model_validator(mode="before")
    def check_sid_and_service_name(cls, values):
        sid = values.get("TEST_ORACLE_SID")
        service_name = values.get("TEST_ORACLE_SERVICE_NAME")
        if (sid is None) == (service_name is None):
            raise ValueError("Connection must have one param: sid or service name")
        return values
