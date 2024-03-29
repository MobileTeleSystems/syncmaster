FROM python:3.11-slim as prod

RUN apt-get update && apt-get install -y \
        libkrb5-dev \
        libsasl2-dev \
        libsasl2-modules-gssapi-mit \
        libsasl2-modules-ldap \
        libsasl2-modules \
        openjdk-17-jdk \
        libssl-dev \
        libldap2-dev \
        autoconf \
        gcc \
        g++ \
        make \
        libnghttp2-dev \
        libffi-dev \
        telnetd \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --timeout 3 --retries 3 poetry && poetry config virtualenvs.create false

WORKDIR /app

COPY ./pyproject.toml ./poetry.lock* /app/

RUN pip install --upgrade pip setuptools wheel packaging

RUN poetry install --no-root --extras "worker"

COPY . /app/

# https://docs.celeryq.dev/en/stable/userguide/workers.html#max-tasks-per-child-setting
# Required to start each Celery task in separated process, avoiding issues with global Spark session object
CMD ["celery", "-A" ,"syncmaster.worker.config.celery", "worker", "--loglevel=info", "--max-tasks-per-child=1"]

FROM prod as test

RUN poetry install --no-root --extras "worker backend" --with test

ENV CREATE_SPARK_SESSION_FUNCTION="tests.spark.get_worker_spark_session.get_worker_spark_session"
# Queue for tests
CMD ["coverage", "run", "-m", "celery", "-A" ,"syncmaster.worker.config.celery", "worker", "--loglevel=info", "--max-tasks-per-child=1", "-Q", "test_queue"]
