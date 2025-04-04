import datetime
import logging

import pytest
from pyspark.sql import DataFrame, SparkSession
from pyspark.sql.types import (
    DateType,
    DoubleType,
    IntegerType,
    StringType,
    StructField,
    StructType,
    TimestampType,
)

from tests.resources.file_df_connection.test_data import data

logger = logging.getLogger(__name__)


@pytest.fixture
def init_df(spark: SparkSession) -> DataFrame:
    logger.info("START INIT DF")
    df_schema = StructType(
        [
            StructField("ID", IntegerType()),
            StructField("PHONE_NUMBER", StringType()),
            StructField("REGION", StringType()),
            StructField("NUMBER", IntegerType()),
            StructField("BIRTH_DATE", DateType()),
            StructField("REGISTERED_AT", TimestampType()),
            StructField("ACCOUNT_BALANCE", DoubleType()),
        ],
    )
    df = spark.createDataFrame(data, schema=df_schema)
    logger.info("END INIT DF")
    return df


@pytest.fixture
def init_df_with_mixed_column_naming(spark: SparkSession) -> DataFrame:
    df_schema = StructType(
        [
            StructField("Id", IntegerType()),
            StructField("Phone Number", StringType()),
            StructField("region", StringType()),
            StructField("NUMBER", IntegerType()),
            StructField("birth_DATE", DateType()),
            StructField("Registered At", TimestampType()),
            StructField("account_balance", DoubleType()),
        ],
    )

    return spark.createDataFrame(
        data=[
            (
                1,
                "+79123456789",
                "Mordor",
                1,
                datetime.date(year=2023, month=3, day=11),
                datetime.datetime.now(),
                1234.2343,
            ),
            (
                2,
                "+79234567890",
                "Gondor",
                2,
                datetime.date(2022, 6, 19),
                datetime.datetime.now(),
                2345.5678,
            ),
            (
                3,
                "+79345678901",
                "Rohan",
                3,
                datetime.date(2021, 11, 5),
                datetime.datetime.now(),
                3456.7890,
            ),
            (
                4,
                "+79456789012",
                "Shire",
                4,
                datetime.date(2020, 1, 30),
                datetime.datetime.now(),
                4567.8901,
            ),
            (
                5,
                "+79567890123",
                "Isengard",
                5,
                datetime.date(2023, 8, 15),
                datetime.datetime.now(),
                5678.9012,
            ),
        ],
        schema=df_schema,
    )
