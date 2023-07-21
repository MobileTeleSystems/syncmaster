FROM sregistry.mts.ru/bigdata/platform/docker-images/python:3.11-slim

RUN pip install --no-cache-dir --timeout 3 --retries 3 poetry \
    && poetry config virtualenvs.create false

WORKDIR /syncmaster

COPY ./syncmaster/pyproject.toml ./syncmaster/poetry.lock* /syncmaster/
RUN poetry export -f requirements.txt --with dev --with test --output /syncmaster/requirements.txt \
    --without-hashes --with-credentials --without-urls \
    && pip install --timeout 5 --retries 5 --no-cache-dir -r /syncmaster/requirements.txt

COPY ./syncmaster/ /syncmaster/

ENV PYTHONPATH=/syncmaster

CMD [ "python", "app/main.py" ]