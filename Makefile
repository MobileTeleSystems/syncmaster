#!make

include .env.local

PIP = .venv/bin/pip
POETRY = .venv/bin/poetry

# Fix docker build and docker compose build using different backends
COMPOSE_DOCKER_CLI_BUILD = 1
DOCKER_BUILDKIT = 1
# Fix docker build on M1/M2
DOCKER_DEFAULT_PLATFORM = linux/amd64

HELP_FUN = \
	%help; while(<>){push@{$$help{$$2//'options'}},[$$1,$$3] \
	if/^([\w-_]+)\s*:.*\#\#(?:@(\w+))?\s(.*)$$/}; \
    print"$$_:\n", map"  $$_->[0]".(" "x(20-length($$_->[0])))."$$_->[1]\n",\
    @{$$help{$$_}},"\n" for keys %help; \

all: help

help: ##@Help Show this help
	@echo -e "Usage: make [target] ...\n"
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)



venv: venv-cleanup  venv-install##@Env Init venv and install poetry dependencies

venv-cleanup: ##@Env Cleanup venv
	@rm -rf .venv || true
	python3.12 -m venv .venv
	${PIP} install -U setuptools wheel pip
	${PIP} install poetry

venv-install: ##@Env Install requirements to venv
	${POETRY} config virtualenvs.create false
	${POETRY} self add poetry-bumpversion
	${POETRY} install --no-root --all-extras --with dev,test,docs $(ARGS)



db: db-start db-upgrade ##@DB Prepare database (in docker)

db-start: ##@DB Start database
	docker compose up -d --wait db $(DOCKER_COMPOSE_ARGS)

db-revision: ##@DB Generate migration file
	${POETRY} run python -m syncmaster.db.migrations revision --autogenerate $(ARGS)

db-upgrade: ##@DB Run migrations to head
	${POETRY} run python -m syncmaster.db.migrations upgrade head $(ARGS)

db-downgrade: ##@DB Downgrade head migration
	${POETRY} run python -m syncmaster.db.migrations downgrade head-1 $(ARGS)


broker: broker-start ##@Broker Prepare broker (in docker)

broker-start: ##Broker Start broker
	docker compose up -d --wait rabbitmq $(DOCKER_COMPOSE_ARGS)



test: test-db test-broker ##@Test Run tests
	${POETRY} run pytest $(PYTEST_ARGS)

test-db: test-db-start df-upgrade db-partitions ##@TestDB Prepare database (in docker)

test-db-start: ##@TestDB Start database
	docker compose -f docker-compose.test.yml up -d --wait db $(DOCKER_COMPOSE_ARGS)

test-broker: test-broker-start ##@TestBroker Prepare broker (in docker)

test-broker-start: ##@TestBroker Start broker
	docker compose -f docker-compose.test.yml up -d --wait rabbitmq $(DOCKER_COMPOSE_ARGS)

test-unit: test-db ##@Test Run unit tests
	${POETRY} run pytest ./tests/test_unit ./tests/test_database $(PYTEST_ARGS)

test-integration-hdfs: test-db ##@Test Run integration tests for HDFS
	docker compose -f docker-compose.test.yml --profile hdfs up -d --wait $(DOCKER_COMPOSE_ARGS)
	${POETRY} run pytest ./tests/test_integration -m hdfs $(PYTEST_ARGS)

test-integration-hive: test-db ##@Test Run integration tests for Hive
	docker compose -f docker-compose.test.yml --profile hive up -d --wait $(DOCKER_COMPOSE_ARGS)
	${POETRY} run pytest ./tests/test_integration -m hive $(PYTEST_ARGS)

test-integration-oracle: test-db ##@Test Run integration tests for Oracle
	docker compose -f docker-compose.test.yml --profile oracle up -d --wait $(DOCKER_COMPOSE_ARGS)
	${POETRY} run pytest ./tests/test_integration -m oracle $(PYTEST_ARGS)

test-integration-s3: test-db ##@Test Run integration tests for S3
	docker compose -f docker-compose.test.yml --profile s3 up -d --wait $(DOCKER_COMPOSE_ARGS)
	${POETRY} run pytest ./tests/test_integration -m s3 $(PYTEST_ARGS)

test-integration: test-db ##@Test Run all integration tests
	docker compose -f docker-compose.test.yml --profile all up -d --wait $(DOCKER_COMPOSE_ARGS)
	${POETRY} run pytest ./tests/test_integration $(PYTEST_ARGS)

test-check-fixtures: ##@Test Check declared fixtures
	${POETRY} run pytest --dead-fixtures $(PYTEST_ARGS)

test-cleanup: ##@Test Cleanup tests dependencies
	docker compose -f docker-compose.test.yml --profile all down $(ARGS)



dev-server: db ##@Application Run development server (without docker)
	${POETRY} run python -m syncmaster.backend $(ARGS)

dev-worker: db broker ##@Application Run development broker (without docker)
	${POETRY} run python -m celery -A syncmaster.worker.config.celery worker --max-tasks-per-child=1 $(ARGS)



prod-build-server: ##@Application Build docker image for server
	docker build --progress=plain -t mtsrus/syncmaster-backend:develop -f ./docker/Dockerfile.backend $(ARGS) .

prod-build-worker: ##@Application Build docker image for worker
	docker build --progress=plain -t mtsrus/syncmaster-worker:develop -f ./docker/Dockerfile.worker $(ARGS) .

prod-build: prod-build-server prod-build-worker ##@Application Build docker images

prod: ##@Application Run production server (with docker)
	docker compose up -d

prod-stop: ##@Application Stop production server
	docker compose down $(ARGS)


.PHONY: docs

docs: docs-build docs-open ##@Docs Generate & open docs

docs-build: ##@Docs Generate docs
	$(MAKE) -C docs html

docs-open: ##@Docs Open docs
	xdg-open docs/_build/html/index.html

docs-cleanup: ##@Docs Cleanup docs
	$(MAKE) -C docs clean

docs-fresh: docs-cleanup docs-build ##@Docs Cleanup & build docs
