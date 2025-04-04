.. _configuration-frontend:

Frontend configuration
======================

API url
-------

SyncMaster UI requires REST API to be accessible from browser. API url is set up using environment variable:

.. code:: bash

    SYNCMASTER__UI__API_BROWSER_URL=http://localhost:8000

If both REST API and frontend are served on the same domain (e.g. through Nginx reverse proxy), for example:

- REST API → ``/api``
- Frontend → ``/``

Then you can use relative path:

.. code:: bash

    SYNCMASTER__UI__API_BROWSER_URL=/api
