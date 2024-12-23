.. _worker-log-url:

Setting the `Run.log_url` value
===============================

Each run in the system is linked to a log URL where the Celery worker logs are available. This log URL might point to an Elastic instance or another logging tool such as Grafana. The log URL is generated based on a template configured in the server.

The configuration parameter is:

.. code-block:: bash

  SYNCMASTER__SERVER__LOG_URL_TEMPLATE=https://grafana.example.com?correlation_id={{ correlation_id }}&run_id={{ run.id }}

You can search for each run by either its correlation id ``x-request-id`` in http headers or the ``Run.Id``.

