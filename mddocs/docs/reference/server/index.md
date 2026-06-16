# REST API Server { #server }

SyncMaster server provides simple REST API for accessing entities stored in [database][server-configuration-database].
Implemented using [FastAPI](https://fastapi.tiangolo.com/).

## Install & run

### With docker

- Install [Docker](https://docs.docker.com/engine/install/)

- Install [docker-compose](https://github.com/docker/compose/releases/)

- Run the following command:

  ```console
  $ docker compose --profile server up -d --wait
  ...
  ```

  `docker-compose` will download all necessary images, create containers, and then start the server.

  Options can be set via `config.yml` file.

### `docker-compose.yml`

```yaml
--8<--
docker-compose.yml:48:75
--8<--
```

### `config.yml`

```yaml
--8<--
config.yml:1:31,40:49,70:71
--8<--
```

- After server is started and ready, open <http://localhost:8000/docs>.

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
  $ pip install data-syncmaster[server]
  ...
  ```

- Run server process

  ```console
  $ python -m syncmaster.server --host 0.0.0.0 --port 8000
  ...
  ```

  This is a thin wrapper around [uvicorn](https://www.uvicorn.org/#command-line-options) cli,
  options and commands are just the same.

- After server is started and ready, open <http://localhost:8000/docs>.

## See also

- [Auth Providers][server-auth-providers]
- [Configuration][server-configuration]
- [CLI for managing superusers][manage-superusers-cli]
- [OpenAPI specification][server-openapi]
