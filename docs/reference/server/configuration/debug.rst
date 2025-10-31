.. _server-configuration-debug:

Enabling debug
===============

Return debug info in REST API responses
---------------------------------------

By default, server does not add error details to response bodies,
to avoid exposing instance-specific information to end users.

With debug enabled:

.. code-block:: yaml
    :caption: config.yml

    server:
        debug: true

.. code-block:: console

    $ curl -XPOST http://localhost:8000/failing/endpoint ...
    {
        "error": {
            "code": "unknown",
            "message": "Got unhandled exception. Please contact support",
            "details": null,
        },
    }

With debug disabled:

.. code-block:: yaml
    :caption: config.yml

    server:
        debug: false

.. code-block:: console

    $ curl -XPOST http://localhost:8000/failing/endpoint ...
    Traceback (most recent call last):
    File ".../uvicorn/protocols/http/h11_impl.py", line 408, in run_asgi
        result = await app(  # type: ignore[func-returns-value]
                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File ".../site-packages/uvicorn/middleware/proxy_headers.py", line 84, in __call__
        return await self.app(scope, receive, send)

.. DANGER::

    This is only for development environment only. Do **NOT** use on production!

Print debug logs on backend
---------------------------

See :ref:`server-configuration-logging`, but replace log level ``INFO`` with ``DEBUG``.

Fill up ``X-Request-ID`` header on backend
------------------------------------------

Server can add ``X-Request-ID`` header to responses, which allows to match request on client with backend response.

This is done by ``request_id`` middleware, which is enabled by default and can configured as described below:

.. autopydantic_model:: syncmaster.server.settings.server.request_id.RequestIDSettings

Print request ID  to backend logs
---------------------------------

This is done by adding a specific filter to logging settings:

.. dropdown:: ``logging.yml``

    .. code-block:: yaml
        :caption: config.yml

        logging:
            filters:
                correlation_id:
                    class: asgi_correlation_id.CorrelationIdFilter
                    uuid_length: 32
                    default_value: '-'

Resulting logs look like:

.. code-block:: text

    2023-12-18 17:14:11.711 uvicorn.access:498 [INFO] 018c15e97a068ae09484f8c25e2799dd 127.0.0.1:34884 - "GET /monitoring/ping HTTP/1.1" 200
