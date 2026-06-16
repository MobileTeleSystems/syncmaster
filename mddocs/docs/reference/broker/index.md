# Message Broker { #message-broker }

Message broker is component used by [REST API Server][server]/[Scheduler][scheduler] to communicate with [Worker][worker].

SyncMaster can work virtually with any broker supported by [Celery](https://docs.celeryq.dev).
But the only broker we tested is [RabbitMQ](https://www.rabbitmq.com/).

## Requirements

- RabbitMQ 4.x. It is recommended to use latest RabbitMQ version.

### Setup

#### With Docker

- Install [Docker](https://docs.docker.com/engine/install/)

- Install [docker-compose](https://github.com/docker/compose/releases/)

- Run the following command:

  ```console
  $ docker compose --profile broker up -d --wait
  ...
  ```

  `docker-compose` will download RabbitMQ image, create container and volume, and then start container.
  Image entrypoint will create database if volume is empty.

  Options can be set via `config.yml` file.

### `docker-compose.yml`

```yaml
--8<--
docker-compose.yml:34:46,134
--8<--
```

### `config.yml`

```yaml
--8<--
config.yml:4:5
--8<--
```

#### Without Docker

Please follow [RabbitMQ installation instruction](https://www.rabbitmq.com/docs/download).
