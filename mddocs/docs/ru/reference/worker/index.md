# Worker { #worker }

SyncMaster worker - это выделенный процесс, который получает новые запуски передачи данных из [брокера сообщений][message-broker],
выполняет их и обновляет статус и URL логов в [базе данных][database]. Реализован с использованием [Celery](https://docs.celeryq.dev).

## ПРИМЕЧАНИЕ

Каждый процесс worker привязан к одной или нескольким очередям. Вы должны создать их перед запуском worker.
Это можно сделать через [Фронтенд][frontend] или через REST API [REST API Сервера][server].

Значение поля `slug` очереди должно быть передано в аргумент Celery `-Q`.
Например, для slug `123-test_queue` это должно быть `-Q 123-test_queue`.

## Установка и запуск

### С использованием docker

- Установите [Docker](https://docs.docker.com/engine/install/)

- Установите [docker-compose](https://github.com/docker/compose/releases/)

- Перейдите в `фронтенд <http://localhost:3000>`

- Создайте новую группу

- Создайте очередь в этой группе, а затем получите **Queue.slug** (например, `123-test_queue`)

- Выполните следующую команду:

  ```console
  $ docker compose --profile worker up -d --wait
  ...
  ```

  `docker-compose` загрузит все необходимые образы, создаст контейнеры, а затем запустит worker.

  Параметры можно установить через файл `.env` или раздел `environment` в `docker-compose.yml`

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
        # список имен пользователей, которым должна быть назначена роль SUPERUSER при запуске приложения
        SYNCMASTER__ENTRYPOINT__SUPERUSERS: admin
        # PROMETHEUS_MULTIPROC_DIR требуется для нескольких рабочих процессов, см.:
        # https://prometheus.github.io/client_python/multiprocess/
        PROMETHEUS_MULTIPROC_DIR: /tmp/prometheus-metrics
      # каталог tmpfs очищается при каждом перезапуске контейнера
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

  # Параметры логирования
  SYNCMASTER__LOGGING__SETUP=True
  SYNCMASTER__LOGGING__PRESET=colored

  # Общие параметры базы данных
  SYNCMASTER__DATABASE__URL=postgresql+asyncpg://syncmaster:changeme@db:5432/syncmaster

  # Шифрование/дешифрование данных учетных записей с использованием этого ключа Fernet.
  # !!! СГЕНЕРИРУЙТЕ СВОЮ СОБСТВЕННУЮ КОПИЮ ДЛЯ ИСПОЛЬЗОВАНИЯ В ПРОДАКШЕНЕ !!!
  SYNCMASTER__ENCRYPTION__SECRET_KEY=UBgPTioFrtH2unlC4XFDiGf5sYfzbdSf_VgiUSaQc94=

  # Общие параметры RabbitMQ
  SYNCMASTER__BROKER__URL=amqp://guest:guest@rabbitmq:5672

  # Параметры сервера
  SYNCMASTER__SERVER__SESSION__SECRET_KEY=generate_some_random_string
  # !!! НИКОГДА НЕ ИСПОЛЬЗУЙТЕ В ПРОДАКШЕНЕ !!!
  SYNCMASTER__SERVER__DEBUG=true

  # Аутентификация Keycloak
  #SYNCMASTER__AUTH__PROVIDER=syncmaster.server.providers.auth.keycloak_provider.KeycloakAuthProvider
  SYNCMASTER__AUTH__KEYCLOAK__SERVER_URL=http://keycloak:8080
  SYNCMASTER__AUTH__KEYCLOAK__REALM_NAME=manually_created
  SYNCMASTER__AUTH__KEYCLOAK__CLIENT_ID=manually_created
  SYNCMASTER__AUTH__KEYCLOAK__CLIENT_SECRET=generated_by_keycloak
  SYNCMASTER__AUTH__KEYCLOAK__REDIRECT_URI=http://localhost:8000/auth/callback
  SYNCMASTER__AUTH__KEYCLOAK__SCOPE=email
  SYNCMASTER__AUTH__KEYCLOAK__VERIFY_SSL=False

  # Фиктивная аутентификация
  SYNCMASTER__AUTH__PROVIDER=syncmaster.server.providers.auth.dummy_provider.DummyAuthProvider
  SYNCMASTER__AUTH__ACCESS_TOKEN__SECRET_KEY=generate_another_random_string

  # Параметры планировщика
  SYNCMASTER__SCHEDULER__TRANSFER_FETCHING_TIMEOUT_SECONDS=200

  # Параметры Worker
  SYNCMASTER__WORKER__LOG_URL_TEMPLATE=https://logs.location.example.com/syncmaster-worker?correlation_id=\{\{ correlation_id \}\}&run_id=\{\{ run.id \}\}
  SYNCMASTER__HWM_STORE__ENABLED=true
  SYNCMASTER__HWM_STORE__TYPE=horizon
  SYNCMASTER__HWM_STORE__URL=http://horizon:8000
  SYNCMASTER__HWM_STORE__NAMESPACE=syncmaster_namespace
  SYNCMASTER__HWM_STORE__USER=admin
  SYNCMASTER__HWM_STORE__PASSWORD=123UsedForTestOnly@!

  # Параметры фронтенда
  SYNCMASTER__UI__API_BROWSER_URL=http://localhost:8000

  # Cors
  SYNCMASTER__SERVER__CORS__ENABLED=True
  SYNCMASTER__SERVER__CORS__ALLOW_ORIGINS=["http://localhost:3000"]
  SYNCMASTER__SERVER__CORS__ALLOW_CREDENTIALS=True
  SYNCMASTER__SERVER__CORS__ALLOW_METHODS=["*"]
  SYNCMASTER__SERVER__CORS__ALLOW_HEADERS=["*"]
  SYNCMASTER__SERVER__CORS__EXPOSE_HEADERS=["X-Request-ID","Location","Access-Control-Allow-Credentials"]
  ```

### Без Docker

- Установите Python 3.11 или выше

- Установите Java 8 или выше

  ```console
  $ yum install java-1.8.0-openjdk-devel  # CentOS 7
  $ dnf install java-11-openjdk-devel  # CentOS 8
  $ apt-get install openjdk-11-jdk  # Debian-based
  ...
  ```

- Настройте [Реляционную базу данных][database], запустите миграции

- Настройте [Брокер сообщений][message-broker]

- Создайте виртуальное окружение

  ```console
  $ python -m venv /some/.venv
  $ source /some/.venv/activate
  ...
  ```

- Установите пакет `syncmaster` со следующими *дополнительными* зависимостями:

  ```console
  $ pip install syncmaster[server,worker]
  ...
  ```

- Запустите [REST API Сервер][server] и [Фронтенд][frontend]

- Создайте новую группу

- Создайте очередь в этой группе, а затем получите **Queue.slug** (например, `123-test_queue`)

- Запустите процесс worker:

  ```console
  $ python -m celery -A syncmaster.worker.celery worker -Q 123-test_queue --max-tasks-per-child=1
  ...
  ```

  Вы можете указать параметры, такие как параллелизм и очереди, добавив дополнительные флаги:

  ```bash
  $ python -m celery -A syncmaster.worker.celery worker -Q 123-test_queue --max-tasks-per-child=1 --concurrency=4 --loglevel=info
  ...
  ```

  Обратитесь к документации [Celery](https://docs.celeryq.dev/en/stable/) для получения информации о более продвинутых опциях запуска.

  > **Флаг `--max-tasks-per-child=1` важен!**
  
## Смотрите также

- [Конфигурация][worker-configuration]
- [Изменение настроек Spark сессии][worker-create-spark-session]
- [Установка значения Run.log_url][worker-log-url]
