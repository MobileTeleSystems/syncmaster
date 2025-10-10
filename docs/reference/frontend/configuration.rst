.. _configuration-frontend:

Frontend configuration
======================

API URL
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

Auth provider
-------------

By default, SyncMaster UI shows login page with username & password fields, designed for :ref:`server-auth-dummy`.
To show a login page for :ref:`keycloak-auth-provider`, you should pass this environment variable to frontend container:

.. code:: bash

    SYNCMASTER__UI__AUTH_PROVIDER=keycloakAuthProvider
