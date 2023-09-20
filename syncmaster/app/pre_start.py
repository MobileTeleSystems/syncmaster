import logging
from time import sleep

from app.config import EnvTypes, Settings, TestSettings

TIMEOUT = 5
COUNT = 12

logger = logging.getLogger(__name__)


def check_test_postgres(settings: Settings, test_settings: TestSettings):
    from onetl.connection import Postgres

    spark = settings.CREATE_SPARK_SESSION_FUNCTION(settings)
    count = COUNT
    connection = Postgres(
        host=test_settings.TEST_POSTGRES_HOST,
        port=test_settings.TEST_POSTGRES_PORT,
        user=test_settings.TEST_POSTGRES_USER,
        password=test_settings.TEST_POSTGRES_PASSWORD,
        database=test_settings.TEST_POSTGRES_DB,
        spark=spark,
    )
    exception = None
    while count > 0:
        try:
            connection.check()
            return
        except Exception:
            count -= 1
            logger.info("Got exception. Will try after %d sec", TIMEOUT)
            sleep(TIMEOUT)
    if exception:
        raise exception


def check_test_oracle(settings: Settings, test_settings: TestSettings):
    from onetl.connection import Oracle

    spark = settings.CREATE_SPARK_SESSION_FUNCTION(settings)
    count = COUNT
    connection = Oracle(
        host=test_settings.TEST_ORACLE_HOST,
        port=test_settings.TEST_ORACLE_PORT,
        user=test_settings.TEST_ORACLE_USER,
        password=test_settings.TEST_ORACLE_PASSWORD,
        service_name=test_settings.TEST_ORACLE_SERVICE_NAME,
        sid=test_settings.TEST_ORACLE_SID,
        spark=spark,
    )
    exception = None
    while count > 0:
        try:
            connection.check()
            return
        except Exception:
            count -= 1
            logger.info("Got exception. Will try after %d sec", TIMEOUT)
            sleep(TIMEOUT)
    if exception:
        raise exception


settings = Settings()

if settings.ENV == EnvTypes.GITLAB:
    test_settings = TestSettings()
    check_test_oracle(settings, test_settings)
    check_test_postgres(settings, test_settings)
