.. _server-auth-providers:

Auth Providers
==============

Syncmaster supports different auth provider implementations. You can change implementation via settings:

.. autopydantic_model:: syncmaster.server.settings.auth.AuthSettings

.. toctree::
    :maxdepth: 2
    :caption: Auth providers

    dummy
    keycloak/index

.. toctree::
    :maxdepth: 2
    :caption: For developers

    custom
