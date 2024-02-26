FROM python:3.12-slim

RUN apt install openjdk-17-jdk
RUN apt install -y install libnghttp2-14

RUN pip install --no-cache-dir --timeout 3 --retries 3 poetry \
    && poetry config virtualenvs.create false

WORKDIR /syncmaster

COPY ./pyproject.toml ./poetry.lock* /syncmaster/
RUN poetry export -f requirements.txt --with backend,dev,test --output /syncmaster/requirements.txt \
    --without-hashes --with-credentials --without-urls \
    && pip install --timeout 5 --retries 5 --no-cache-dir -r /syncmaster/requirements.txt

COPY ./syncmaster/ /syncmaster/

ENV PYTHONPATH=/syncmaster

CMD [ "python", "app/main.py" ]