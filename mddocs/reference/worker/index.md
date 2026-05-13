# Worker { #worker }

SyncMaster worker is a dedicated process which receives new transfer Runs from [message-broker][message-broker],
executes them and updates status & log url in [database][database]. Implemented using [Celery](https://docs.celeryq.dev).

## NOTE

Each worker process is bound to one or more Queues. You have to created it before starting a worker.
This can be done via [Frontend][frontend] or via [REST API Server][server] REST API.

Queue field `slug` value is then should be passed to Celery argument `-Q`.
For example, for slug `123-test_queue` this should be `-Q 123-test_queue`.

## Install & run

### With docker

- Install [Docker](https://docs.docker.com/engine/install/)

- Install [docker-compose](https://github.com/docker/compose/releases/)

- Go to `frontend <http://localhost:3000>`

- Create new Group

- Create Queue in this group, and then get **Queue.slug** (e.g. `123-test_queue`)

- Run the following command:

  ```console
  $ docker compose --profile worker up -d --wait
  ...
  ```

  `docker-compose` will download all necessary images, create containers, and then start the worker.

  Options can be set via `config.yml` file.

### `docker-compose.yml`

--8<--
docker-compose.yml:77:96
--8<--

### `config.yml`

--8<--
config.yml:1:10,57:67
--8<--

### Without docker

- Install Python 3.11 or above

- Install Java 8 or above

  ```console
  $ yum install java-1.8.0-openjdk-devel  # CentOS 7
  $ dnf install java-11-openjdk-devel  # CentOS 8
  $ apt-get install openjdk-11-jdk  # Debian-based
  ...
  ```

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
  $ pip install data-syncmaster[server,worker]
  ...
  ```

- Start [REST API Server][server] and [Frontend][frontend]

- Create new Group

- Create Queue in this group, and then get **Queue.slug** (e.g. `123-test_queue`)

- Run worker process:

  ```console
  $ python -m celery -A syncmaster.worker.celery worker -Q 123-test_queue --max-tasks-per-child=1
  ...
  ```

  You can specify options like concurrency and queues by adding additional flags:

  ```bash
  $ python -m celery -A syncmaster.worker.celery worker -Q 123-test_queue --max-tasks-per-child=1 --concurrency=4 --loglevel=info
  ...
  ```

  Refer to the [Celery](https://docs.celeryq.dev/en/stable/) documentation for more advanced start options.

  !!! note
      `--max-tasks-per-child=1` flag is important!

## See also

- [Configuration][worker-configuration]
- [Altering Spark session settings][worker-create-spark-session]
- [Setting the Run.log_url value][worker-log-url]
