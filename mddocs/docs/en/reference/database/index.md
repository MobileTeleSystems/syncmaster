# Relation Database { #database }

SyncMaster requires relational database for storing internal data.

Currently, SyncMaster supports only [PostgreSQL](https://www.postgresql.org/).

## Migrations

After a database is started, it is required to run migration script.
For empty database, it creates all the required tables and indexes.
For non-empty database, it will perform database structure upgrade, using [Alembic](https://alembic.sqlalchemy.org/).

### WARNING

Other containers (server, scheduler, worker) should be stopped while running migrations, to prevent interference.

## Requirements

- PostgreSQL 12 or higher. It is recommended to use latest Postgres version.

## Install & run

### With Docker

- Install [Docker](https://docs.docker.com/engine/install/)

- Install [docker-compose](https://github.com/docker/compose/releases/)

- Run the following command:

  ```console
  $ docker compose up -d db db-migrations
  ...
  ```

  `docker-compose` will download PostgreSQL image, create container and volume, and then start container.
  Image entrypoint will create database if volume is empty.

  After that, one-off container with migrations script will run.

  Options can be set via `.env` file or `environment` section in `docker-compose.yml`

### `docker-compose.yml`

  ```default
  services:
    db:
      image: postgres:17
      restart: unless-stopped
      environment:
        POSTGRES_DB: syncmaster
        POSTGRES_USER: syncmaster
        POSTGRES_PASSWORD: changeme
      ports:
        - 5432:5432
      volumes:
        - postgres_data:/var/lib/postgresql/data
      healthcheck:
        test: pg_isready
        start_period: 5s
        interval: 30s
        timeout: 5s
        retries: 3

    db-migrations:
      image: mtsrus/syncmaster-server:${VERSION:-develop}
      restart: no
      build:
        dockerfile: docker/Dockerfile.server
        context: .
        target: prod
      entrypoint: [python, -m, syncmaster.db.migrations, upgrade, head]
      env_file: .env.docker
      depends_on:
        db:
          condition: service_healthy

    rabbitmq:
      image: rabbitmq:4
      restart: unless-stopped
      ports:
        - 5672:5672
      volumes:
        - rabbitmq_data:/var/lib/rabbitmq
      healthcheck:
        test: rabbitmq-diagnostics -q ping
        start_period: 5s
        interval: 30s
        timeout: 5s
        retries: 3

    server:
      image: mtsrus/syncmaster-server:${VERSION:-develop}
      restart: unless-stopped
      build:
        dockerfile: docker/Dockerfile.server
        context: .
        target: prod
      ports:
        - 8000:8000
      environment:
        # list here usernames which should be assigned SUPERUSER role on application start
        SYNCMASTER__ENTRYPOINT__SUPERUSERS: admin
        # PROMETHEUS_MULTIPROC_DIR is required for multiple workers, see:
        # https://prometheus.github.io/client_python/multiprocess/
        PROMETHEUS_MULTIPROC_DIR: /tmp/prometheus-metrics
      # tmpfs dir is cleaned up each container restart
      tmpfs:
        - /tmp/prometheus-metrics:mode=1777
      env_file: .env.docker
      depends_on:
        db:
          condition: service_healthy
        db-migrations:
          condition: service_completed_successfully
        rabbitmq:
          condition: service_healthy
      profiles:
        - server
        - frontend
        - all

    worker:
      image: mtsrus/syncmaster-worker:${VERSION:-develop}
      restart: unless-stopped
      build:
        dockerfile: docker/Dockerfile.worker
        context: .
        target: prod
      env_file: .env.docker
      command: --loglevel=info -Q 123-test_queue  # Queue.slug
      depends_on:
        db:
          condition: service_healthy
        db-migrations:
          condition: service_completed_successfully
        rabbitmq:
          condition: service_healthy
      profiles:
        - worker
        - all

    scheduler:
      image: mtsrus/syncmaster-scheduler:${VERSION:-develop}
      restart: unless-stopped
      build:
        dockerfile: docker/Dockerfile.scheduler
        context: .
        target: prod
      env_file: .env.docker
      depends_on:
        db:
          condition: service_healthy
        db-migrations:
          condition: service_completed_successfully
        rabbitmq:
          condition: service_healthy
      profiles:
        - scheduler
        - all

    frontend:
      image: mtsrus/syncmaster-ui:${VERSION:-develop}
      restart: unless-stopped
      env_file: .env.docker
      ports:
        - 3000:3000
      depends_on:
        server:
          condition: service_healthy
      profiles:
        - frontend
        - all

  volumes:
    postgres_data:
    rabbitmq_data:
  ```

### `.env.docker`

  ```default
  TZ=UTC
  ENV=LOCAL

  # Logging options
  SYNCMASTER__LOGGING__SETUP=True
  SYNCMASTER__LOGGING__PRESET=colored

  # Common DB options
  SYNCMASTER__DATABASE__URL=postgresql+asyncpg://syncmaster:changeme@db:5432/syncmaster

  # Encrypt / Decrypt credentials data using this Fernet key.
  # !!! GENERATE YOUR OWN COPY FOR PRODUCTION USAGE !!!
  SYNCMASTER__ENCRYPTION__SECRET_KEY=UBgPTioFrtH2unlC4XFDiGf5sYfzbdSf_VgiUSaQc94=

  # Common RabbitMQ options
  SYNCMASTER__BROKER__URL=amqp://guest:guest@rabbitmq:5672

  # Server options
  SYNCMASTER__SERVER__SESSION__SECRET_KEY=generate_some_random_string
  # !!! NEVER USE ON PRODUCTION !!!
  SYNCMASTER__SERVER__DEBUG=true

  # Keycloak Auth
  #SYNCMASTER__AUTH__PROVIDER=syncmaster.server.providers.auth.keycloak_provider.KeycloakAuthProvider
  SYNCMASTER__AUTH__KEYCLOAK__SERVER_URL=http://keycloak:8080
  SYNCMASTER__AUTH__KEYCLOAK__REALM_NAME=manually_created
  SYNCMASTER__AUTH__KEYCLOAK__CLIENT_ID=manually_created
  SYNCMASTER__AUTH__KEYCLOAK__CLIENT_SECRET=generated_by_keycloak
  SYNCMASTER__AUTH__KEYCLOAK__REDIRECT_URI=http://localhost:8000/auth/callback
  SYNCMASTER__AUTH__KEYCLOAK__SCOPE=email
  SYNCMASTER__AUTH__KEYCLOAK__VERIFY_SSL=False

  # Dummy Auth
  SYNCMASTER__AUTH__PROVIDER=syncmaster.server.providers.auth.dummy_provider.DummyAuthProvider
  SYNCMASTER__AUTH__ACCESS_TOKEN__SECRET_KEY=generate_another_random_string

  # Scheduler options
  SYNCMASTER__SCHEDULER__TRANSFER_FETCHING_TIMEOUT_SECONDS=200

  # Worker options
  SYNCMASTER__WORKER__LOG_URL_TEMPLATE=https://logs.location.example.com/syncmaster-worker?correlation_id=\{\{ correlation_id \}\}&run_id=\{\{ run.id \}\}
  SYNCMASTER__HWM_STORE__ENABLED=true
  SYNCMASTER__HWM_STORE__TYPE=horizon
  SYNCMASTER__HWM_STORE__URL=http://horizon:8000
  SYNCMASTER__HWM_STORE__NAMESPACE=syncmaster_namespace
  SYNCMASTER__HWM_STORE__USER=admin
  SYNCMASTER__HWM_STORE__PASSWORD=123UsedForTestOnly@!

  # Frontend options
  SYNCMASTER__UI__API_BROWSER_URL=http://localhost:8000

  # Cors
  SYNCMASTER__SERVER__CORS__ENABLED=True
  SYNCMASTER__SERVER__CORS__ALLOW_ORIGINS=["http://localhost:3000"]
  SYNCMASTER__SERVER__CORS__ALLOW_CREDENTIALS=True
  SYNCMASTER__SERVER__CORS__ALLOW_METHODS=["*"]
  SYNCMASTER__SERVER__CORS__ALLOW_HEADERS=["*"]
  SYNCMASTER__SERVER__CORS__EXPOSE_HEADERS=["X-Request-ID","Location","Access-Control-Allow-Credentials"]
  ```

### Without Docker

- For installing PostgreSQL, please follow [installation instruction](https://www.postgresql.org/download/).

- Install Python 3.11 or above

- Create virtual environment

  ```console
  $ python -m venv /some/.venv  
  $ source /some/.venv/activate
  ...
  ```

- Install `syncmaster` package with following *extra* dependencies:

  ```console
  $ pip install syncmaster[postgres]
  ...
  ```

- Configure [Database connection][configuration-database] using environment variables, e.g. by creating `.env` file:

  ```console
  $ export SYNCMASTER__DATABASE__URL=postgresql+asyncpg://syncmaster:changeme@db:5432/syncmaster
  ...
  ```

  And then read values from this file:

  ```console
  $ source /some/.env
  ...
  ```

- Run migrations:

  ```console
  $ python -m syncmaster.db.migrations upgrade head
  ...
  ```

  This is a thin wrapper around [alembic cli](https://alembic.sqlalchemy.org/en/latest/tutorial.html#running-our-first-migration),
  options and commands are just the same.

> **This command should be executed after each upgrade to new Data.SyncMaster version.**

## See also

- [Database settings][configuration-database]
- [Credentials encryption][configuration-credentials-encryption]
- [Database structure][database-structure]
