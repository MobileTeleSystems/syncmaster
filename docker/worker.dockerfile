FROM python:3.12-slim as prod

RUN apt update && sudo apt upgrade
RUN apt install telnetd
RUN apt install openjdk-17-jdk
RUN apt install -y install libnghttp2-14
RUN pip install --no-cache-dir --timeout 3 --retries 3 poetry && poetry config virtualenvs.create false

WORKDIR /syncmaster

COPY ./pyproject.toml ./poetry.lock* /syncmaster/
RUN poetry export -f requirements.txt --with worker --output /syncmaster/requirements.txt \
    --without-hashes --with-credentials --without-urls \
    && pip install --timeout 5 --retries 5 --no-cache-dir -r /syncmaster/requirements.txt

COPY ./syncmaster/ /syncmaster/


# https://docs.celeryq.dev/en/stable/userguide/workers.html#max-tasks-per-child-setting
# Required to start each Celery task in separated process, avoiding issues with global Spark session object
CMD ["celery", "-A" ,"app.tasks.config.celery", "worker", "--loglevel=info", "--max-tasks-per-child=1"]

FROM prod as test

ENV CREATE_SPARK_SESSION_FUNCTION="tests.spark.get_worker_spark_session.get_worker_spark_session"
# Queue for tests
CMD ["celery", "-A" ,"app.tasks.config.celery", "worker", "--loglevel=info", "--max-tasks-per-child=1", "-Q", "test_queue"]
