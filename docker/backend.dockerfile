FROM python:3.11-slim

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
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --timeout 3 --retries 3 poetry \
    && poetry config virtualenvs.create false

WORKDIR /syncmaster

COPY ./pyproject.toml ./poetry.lock* /syncmaster/
RUN poetry install --no-root --only backend

COPY ./syncmaster/ /syncmaster/

ENV PYTHONPATH=/syncmaster

CMD [ "python", "app/main.py" ]