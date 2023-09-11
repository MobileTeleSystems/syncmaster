FROM sregistry.mts.ru/bigdata/platform/docker-images/python:3.11-slim

RUN curl https://download.java.net/java/GA/jdk20.0.2/6e380f22cbe7469fa75fb448bd903d8e/9/GPL/openjdk-20.0.2_linux-x64_bin.tar.gz --output open-jdk.tar.gz \
    && tar -zxf ./open-jdk.tar.gz -C /opt/ \
    && rm -rf ./open-jdk.tar.gz

ENV PATH=$PATH:/opt/openjdk

RUN pip install --no-cache-dir --timeout 3 --retries 3 poetry \
    && poetry config virtualenvs.create false

WORKDIR /syncmaster

COPY ./pyproject.toml ./poetry.lock* /syncmaster/
RUN poetry export -f requirements.txt --with dev --with test --output /syncmaster/requirements.txt \
    --without-hashes --with-credentials --without-urls \
    && pip install --timeout 5 --retries 5 --no-cache-dir -r /syncmaster/requirements.txt

COPY ./syncmaster/ /syncmaster/