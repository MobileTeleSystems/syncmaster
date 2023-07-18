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
	python3.11 -m venv .venv && \
	.venv/bin/pip install poetry && \
	cd ${APP_PATH} && \
	../${POETRY} install --no-root

env: ##@Env Create .env file
	@cp .env.dev .env
	@echo "File .env was created. Remember to replace passwords for security"

help: ##@Help Show this help
	@echo -e "Usage: make [target] ...\n"
	@perl -e '$(HELP_FUN)' $(MAKEFILE_LIST)

run: ##@Application Run backend locally (without docker)
	@cd ./${APP_PATH} && \
	POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_DB=${POSTGRES_DB} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	PYTHONPATH=. \
	../${POETRY} run python app/main.py

revision: ##@Database Create new revision of migrations
	@cd ./${APP_PATH} && \
	POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_DB=${POSTGRES_DB} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	PYTHONPATH=. \
	../${POETRY} run alembic revision --autogenerate

migrate: ##@Database Upgdade database to last migration
	@cd ./${APP_PATH} && \
	POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_DB=${POSTGRES_DB} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	PYTHONPATH=. \
	../${POETRY} run alembic upgrade head

test: ##@Test Run tests
	@cd ./${APP_PATH} && \
	POSTGRES_HOST=${POSTGRES_HOST} \
	POSTGRES_PORT=${POSTGRES_PORT} \
	POSTGRES_DB=${POSTGRES_DB} \
	POSTGRES_USER=${POSTGRES_USER} \
	POSTGRES_PASSWORD=${POSTGRES_PASSWORD} \
	PYTHONPATH=. \
	../${POETRY} run pytest -x -vv ./tests