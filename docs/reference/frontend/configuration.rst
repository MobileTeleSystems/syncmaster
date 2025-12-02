.. _configuration-frontend:

Frontend configuration
======================

API URL
-------

SyncMaster UI requires REST API to be accessible from browser. API url is set up using config file:

.. code-block:: yaml
    :caption: config.yml

    ui:
        api_browser_url: http://localhost:8000

If both REST API and frontend are served on the same domain (e.g. through Nginx reverse proxy), for example:

- REST API → ``/api``
- Frontend → ``/``

Then you can use relative path:

.. code-block:: yaml
    :caption: config.yml

    ui:
        api_browser_url: /api

Auth provider
-------------

By default, SyncMaster UI shows login page with username & password fields, designed for :ref:`server-auth-dummy`.
To show a login page for :ref:`keycloak-auth-provider`, you should set config option:

.. code-block:: yaml
    :caption: config.yml

    ui:
        auth_provider: keycloakAuthProvider
        # auth_provider: dummyAuthProvider
