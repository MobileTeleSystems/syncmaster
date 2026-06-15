# Frontend { #frontend }

SyncMaster provides a [Frontend (UI)](https://github.com/MTSWebServices/syncmaster-ui) based on [React](https://react.dev/),
providing users the ability to create, update, delete entities.

## Install & run

### With Docker

- Install [Docker](https://docs.docker.com/engine/install/)

- Install [docker-compose](https://github.com/docker/compose/releases/)

- Run the following command:

  ```console
  $ docker compose --profile frontend up -d --wait
  ...
  ```

  `docker-compose` will download SyncMaster UI image, create containers, and then start them.

  Options can be set via  `config.yml` file.

### `docker-compose.yml`

```yaml
--8<--
docker-compose.yml:120:132
--8<--
```

### `config.yml`

```yaml
--8<--
config.yml:34:37
--8<--
```

- After frontend is started and ready, open [http://localhost:3000](http://localhost:3000).

## See also

- [Frontend configuration][configuration-frontend]
