ifeq ($(shell test -e '.env' && echo -n yes),yes)
	include .env
endif

APP_PATH = ./syncmaster

POETRY = ./.venv/bin/poetry

HELP_FUN = \
	%help; while(<>){push@{$$help{$$2//'options'}},[$$1,$$3] \
	if/^([\w-_]+)\s*:.*\#\#(?:@(\w+))?\s(.*)$$/}; \
    print"$$_:\n", map"  $$_->[0]".(" "x(20-length($$_->[0])))."$$_->[1]\n",\
    @{$$help{$$_}},"\n" for keys %help; \

venv: ##@Env Init venv and install poetry dependencies
	@rm -rf .venv || true && \
	python3.12 -m venv .venv && \
	.venv/bin/pip install poetry && \
	${POETRY} install --no-root

env: ##@Env Create .env file
	@cp .env.dev .env
	@echo "File .env was created. Remember to replace passwords for security"

help: ##@Help Show this help
	@echo -e "Usage: make [target] ...\n"
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)

run: ##@Application Run backend locally (without docker)
	@POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_DB=${POSTGRES_DB} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	RABBITMQ_HOST=${RABIITMQ_HOST} \
	RABBITMQ_PORT=${RABBITMQ_PORT} \
	RABBITMQ_USER=${RABBITMQ_USER} \
	RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD} \
	PYTHONPATH=${APP_PATH} \
	${POETRY} run python ./syncmaster/backend/main.py

revision: ##@Database Create new revision of migrations
	@POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_DB=${POSTGRES_DB} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	RABBITMQ_HOST=${RABIITMQ_HOST} \
	RABBITMQ_PORT=${RABBITMQ_PORT} \
	RABBITMQ_USER=${RABBITMQ_USER} \
	RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD} \
	PYTHONPATH=${APP_PATH} \
	${POETRY} run python -m syncmaster.db.migrations --autogenerate

migrate: ##@Database Upgdade database to last migration
	@POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_DB=${POSTGRES_DB} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	RABBITMQ_HOST=${RABIITMQ_HOST} \
	RABBITMQ_PORT=${RABBITMQ_PORT} \
	RABBITMQ_USER=${RABBITMQ_USER} \
	RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD} \
	PYTHONPATH=${APP_PATH} \
	${POETRY} run python -m syncmaster.db.migrations upgrade head

test: ##@Test Run tests
	@POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_DB=${POSTGRES_DB} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	RABBITMQ_HOST=${RABIITMQ_HOST} \
	RABBITMQ_PORT=${RABBITMQ_PORT} \
	RABBITMQ_USER=${RABBITMQ_USER} \
	RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD} \
	TEST_POSTGRES_USER=${TEST_POSTGRES_USER} \
	TEST_POSTGRES_PASSWORD=${TEST_POSTGRES_PASSWORD} \
	TEST_POSTGRES_HOST=${TEST_POSTGRES_HOST} \
	TEST_POSTGRES_PORT=${TEST_POSTGRES_PORT} \
	TEST_POSTGRES_DB=${TEST_POSTGRES_DB} \
	TEST_ORACLE_HOST=${TEST_ORACLE_HOST} \
	TEST_ORACLE_PORT=${TEST_ORACLE_PORT} \
	TEST_ORACLE_USER=${TEST_ORACLE_USER} \
	TEST_ORACLE_PASSWORD=${TEST_ORACLE_PASSWORD} \
	TEST_ORACLE_SERVICE_NAME=${TEST_ORACLE_SERVICE_NAME} \
	TEST_HIVE_CLUSTER=${TEST_HIVE_CLUSTER} \
	SPARK_CONF_DIR=${SPARK_CONF_DIR} \
	HADOOP_CONF_DIR=${HADOOP_CONF_DIR} \
	HIVE_CONF_DIR=${HIVE_CONF_DIR} \
	PYTHONPATH=${APP_PATH} \
	${POETRY}  run pytest

check-fixtures: ##@Test Check declared fixtures without using
	@POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_DB=${POSTGRES_DB} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	RABBITMQ_HOST=${RABIITMQ_HOST} \
	RABBITMQ_PORT=${RABBITMQ_PORT} \
	RABBITMQ_USER=${RABBITMQ_USER} \
	RABBITMQ_PASSWORD=${RABBITMQ_PASSWORD} \
	PYTHONPATH=${APP_PATH} \
	${POETRY} run pytest --dead-fixtures

run_back_docker:
	docker run --env-file ./.env.docker \
	-v .:/app \
	-v ./cached_jars:/root/.ivy2 \
	--net syncmaster_network -p 8000:8000 --rm \
	 -it --name backend syncmaster_back /bin/bash

run_worker_docker:
	docker run --env-file ./.env.docker \
	-v .:/app \
	-v ./cached_jars:/root/.ivy2 \
	--net syncmaster_network --rm \
	-it --name worker syncmaster_worker /bin/bash

# Necessary because the command and directory have the same name 'docs'
.PHONY: docs

docs: docs-build docs-open ##@Docs Generate & open docs

docs-build: ##@Docs Generate docs
	$(MAKE) -C docs html

docs-open: ##@Docs Open docs
	xdg-open docs/_build/html/index.html

docs-cleanup: ##@Docs Cleanup docs
	$(MAKE) -C docs clean

docs-fresh: docs-cleanup docs-build ##@Docs Cleanup & build docs
