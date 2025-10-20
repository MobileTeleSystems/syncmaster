# Enabling debug { #server-configuration-debug }

## Return debug info in REST API responses

By default, server does not add error details to response bodies,
to avoid exposing instance-specific information to end users.

You can change this by setting:

```console
$ export SYNCMASTER__SERVER__DEBUG=False
$ # start REST API server
$ curl -XPOST http://localhost:8000/failing/endpoint ...
{
    "error": {
        "code": "unknown",
        "message": "Got unhandled exception. Please contact support",
        "details": null,
    },
}
```

```console
$ export SYNCMASTER__SERVER__DEBUG=True
$ # start REST API server
$ curl -XPOST http://localhost:8000/failing/endpoint ...
Traceback (most recent call last):
File ".../uvicorn/protocols/http/h11_impl.py", line 408, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
File ".../site-packages/uvicorn/middleware/proxy_headers.py", line 84, in __call__
    return await self.app(scope, receive, send)
```

## DANGER

This is only for development environment only. Do **NOT** use on production!

## Print debug logs on backend

See [Logging settings][server-configuration-logging], but replace log level `INFO` with `DEBUG`.

## Fill up `X-Request-ID` header on backend

Server can add `X-Request-ID` header to responses, which allows to match request on client with backend response.

This is done by `request_id` middleware, which is enabled by default and can configured as described below:

::: syncmaster.server.settings.server.request_id.RequestIDSettings

## Print request ID to backend logs

This is done by adding a specific filter to logging handler:

### `logging.yml`

```default
# development usage only
version: 1
disable_existing_loggers: false

filters:
  # Add request ID as extra field named `correlation_id` to each log record.
  # This is used in combination with settings.server.request_id.enabled=True
  # See https://github.com/snok/asgi-correlation-id#configure-logging
  correlation_id:
    (): asgi_correlation_id.CorrelationIdFilter
    uuid_length: 32
    default_value: '-'

formatters:
  plain:
    (): logging.Formatter
    # Add correlation_id to log records
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

Resulting logs look like:

```text
2023-12-18 17:14:11.711 uvicorn.access:498 [INFO] 018c15e97a068ae09484f8c25e2799dd 127.0.0.1:34884 - "GET /monitoring/ping HTTP/1.1" 200
```
