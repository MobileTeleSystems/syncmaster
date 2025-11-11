# Включение отладки { #server-configuration-debug }

## Возврат отладочной информации в ответах REST API

По умолчанию сервер не добавляет детали ошибок в тело ответа,
чтобы избежать раскрытия информации, специфичной для инстанса, конечным пользователям.

Вы можете изменить это, установив:

```console
$ export SYNCMASTER__SERVER__DEBUG=False
$ # запуск сервера REST API
$ curl -XPOST http://localhost:8000/failing/endpoint ...
{
    "error": {
        "code": "unknown",
        "message": "Получено необработанное исключение. Пожалуйста, обратитесь в службу поддержки",
        "details": null,
    },
}
```

```console
$ export SYNCMASTER__SERVER__DEBUG=True
$ # запуск сервера REST API
$ curl -XPOST http://localhost:8000/failing/endpoint ...
Traceback (most recent call last):
File ".../uvicorn/protocols/http/h11_impl.py", line 408, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File ".../site-packages/uvicorn/middleware/proxy_headers.py", line 84, in __call__
    return await self.app(scope, receive, send)
```

## ОПАСНО

Это только для среды разработки. **НЕ** используйте в продакшене!

## Вывод отладочных логов на бэкенде

См. [Настройки логирования][server-configuration-logging], но замените уровень логирования `INFO` на `DEBUG`.

## Заполнение заголовка `X-Request-ID` на бэкенде

Сервер может добавлять заголовок `X-Request-ID` к ответам, что позволяет сопоставлять запросы на клиенте с ответами бэкенда.

Это делается с помощью промежуточного ПО `request_id`, которое включено по умолчанию и может быть настроено, как описано ниже:

::: syncmaster.server.settings.server.request_id.RequestIDSettings

## Вывод идентификатора запроса в логи бэкенда

Это делается путем добавления специального фильтра к обработчику логирования:

### `logging.yml`

```default
# только для разработки
version: 1
disable_existing_loggers: false

filters:
  # Добавляет идентификатор запроса как дополнительное поле с именем `correlation_id` к каждой записи лога.
  # Это используется в сочетании с settings.server.request_id.enabled=True
  # См. https://github.com/snok/asgi-correlation-id#configure-logging
  correlation_id:
    (): asgi_correlation_id.CorrelationIdFilter
    uuid_length: 32
    default_value: '-'

formatters:
  plain:
    (): logging.Formatter
    # Добавление correlation_id к записям лога
    fmt: '%(asctime)s.%(msecs)03d %(processName)s:%(process)d %(name)s:%(lineno)d [%(levelname)s] %(correlation_id)s %(message)s'
    datefmt: '%Y-%m-%d %H:%M:%S'

handlers:
  main:
    class: logging.StreamHandler
    formatter: plain
    filters: [correlation_id]
    stream: ext://sys.stdout
  celery:
    class: logging.StreamHandler
    formatter: plain
    filters: [correlation_id]
    stream: ext://sys.stdout

loggers:
  '':
    handlers: [main]
    level: INFO
    propagate: false
  uvicorn:
    handlers: [main]
    level: INFO
    propagate: false
  celery:
    level: INFO
    handlers: [celery]
    propagate: false
  scheduler:
    handlers: [main]
    level: INFO
    propagate: false
  py4j:
    handlers: [main]
    level: WARNING
    propagate: false
  hdfs.client:
    handlers: [main]
    level: WARNING
    propagate: false
```

Получаемые логи выглядят так:

```text
2023-12-18 17:14:11.711 uvicorn.access:498 [INFO] 018c15e97a068ae09484f8c25e2799dd 127.0.0.1:34884 - "GET /monitoring/ping HTTP/1.1" 200
```
