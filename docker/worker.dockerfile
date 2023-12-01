FROM sregistry.mts.ru/bigdata/platform/docker-images/python:3.11-slim

RUN microdnf install java-17-openjdk libnghttp2-1.33.0-3.el8_2.1  # fix version https://github.com/nghttp2/nghttp2/issues/2003

RUN pip install --no-cache-dir --timeout 3 --retries 3 poetry \
    && poetry config virtualenvs.create false

WORKDIR /syncmaster

COPY ./pyproject.toml ./poetry.lock* /syncmaster/
RUN poetry export -f requirements.txt --with worker --output /syncmaster/requirements.txt \
    --without-hashes --with-credentials --without-urls \
    && pip install --timeout 5 --retries 5 --no-cache-dir -r /syncmaster/requirements.txt

COPY ./syncmaster/ /syncmaster/

# https://docs.celeryq.dev/en/stable/userguide/workers.html#max-tasks-per-child-setting
# Required to start each Celery task in separated process, avoiding issues with global Spark session object
CMD ["celery", "-A" ,"app.tasks.config.celery" ,"worker", "--loglevel=info", "--max-tasks-per-child=1", "-Q", "test_queue"]
