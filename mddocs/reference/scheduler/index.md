# Scheduler { #scheduler }

SyncMaster scheduler is a dedicated process which periodically checks scheduler Transfers in [database][database],
and creates corresponding Runs in [message-broker][message-broker].

Implemented using [APScheduler](https://github.com/agronholm/apscheduler).

## Install & run

### With docker

- Install [Docker](https://docs.docker.com/engine/install/)

- Install [docker-compose](https://github.com/docker/compose/releases/)

- Run the following command:

  ```console
  $ docker compose --profile scheduler up -d --wait
  ...
  ```

  `docker-compose` will download all necessary images, create containers, and then start the scheduler.

  Options can be set via  `config.yml` file.

### `docker-compose.yml`

--8<--
docker-compose.yml:98:116
--8<--

### `config.yml`

--8<--
config.yml:1:10,57:58
--8<--

### Without docker

- Install Python 3.11 or above

- Setup [Relation Database][database], run migrations

- Setup [Message Broker][message-broker]

- Create virtual environment

  ```console
  $ python -m venv /some/.venv
  $ source /some/.venv/activate
  ...
  ```

- Install `syncmaster` package with following *extra* dependencies:

  ```console
  $ pip install data-syncmaster[scheduler]
  ...
  ```

- Run scheduler process:

  ```console
  $ python -m syncmaster.Scheduler
  ...
  ```

  Scheduler currently don't have any command line arguments.

## See also

- [Configuration][scheduler-configuration]
