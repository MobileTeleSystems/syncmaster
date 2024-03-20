# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
import logging
from time import sleep

from syncmaster.config import Settings, TestSettings
from tests.test_integration.test_run_transfer.conftest import get_spark_session

TIMEOUT = 5
COUNT = 12

logger = logging.getLogger(__name__)


def check_test_postgres(settings: Settings, test_settings: TestSettings) -> None:
    from onetl.connection import Postgres

    spark_session = get_spark_session(settings)

    count = COUNT
    connection = Postgres(
        host=test_settings.TEST_POSTGRES_HOST,
        port=test_settings.TEST_POSTGRES_PORT,
        user=test_settings.TEST_POSTGRES_USER,
        password=test_settings.TEST_POSTGRES_PASSWORD,
        database=test_settings.TEST_POSTGRES_DB,
        spark=spark_session,
    )
    exception = None
    while count > 0:
        try:
            connection.check()
            return
        except Exception:
            count -= 1
            logger.info("Got exception on postgres. Will try after %d sec", TIMEOUT)
            sleep(TIMEOUT)
    if exception:
        raise exception


def check_test_oracle(settings: Settings, test_settings: TestSettings) -> None:
    from onetl.connection import Oracle

    spark_session = get_spark_session(settings)

    count = COUNT
    connection = Oracle(
        host=test_settings.TEST_ORACLE_HOST,
        port=test_settings.TEST_ORACLE_PORT,
        user=test_settings.TEST_ORACLE_USER,
        password=test_settings.TEST_ORACLE_PASSWORD,
        service_name=test_settings.TEST_ORACLE_SERVICE_NAME,
        sid=test_settings.TEST_ORACLE_SID,
        spark=spark_session,
    )
    exception = None
    while count > 0:
        try:
            connection.check()
            return
        except Exception:
            count -= 1
            logger.info("Got exception on oracle. Will try after %d sec", TIMEOUT)
            sleep(TIMEOUT)
    if exception:
        raise exception


def check_test_hive(settings: Settings, test_settings: TestSettings) -> None:
    from onetl.connection import Hive

    spark_session = get_spark_session(settings)

    count = COUNT
    connection = Hive(
        cluster=test_settings.TEST_HIVE_CLUSTER,
        spark=spark_session,
    )
    exception = None
    while count > 0:
        try:
            connection.check()
            connection.execute("SHOW DATABASES")
            return
        except Exception:
            count -= 1
            logger.info("Got exception on hive. will try after %d sec", TIMEOUT)
            sleep(TIMEOUT)
    if exception:
        raise exception


settings = Settings()
