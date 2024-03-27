.. _role-permissions:

Role Permissions
================

syncmaster implements a role-based access control model to manage permissions across different entities in the service.

Role Model Overview
-------------------

Roles are defined within the context of namespaces, with the exception of the superadmin role. A user can be associated with one, several, or no namespaces at all.

- **GUEST**: User without a specific namespace assignment, having limited access rights. This is a default role.
- **DEVELOPER**: Users with development-related permissions.
- **MAINTAINER**: Users with permissions similar to developers but with additional rights in certain areas.
- **OWNER**: Users with full permissions within their owned namespaces and associated HWMs.
- **SUPERADMIN**: Users with full system-wide permissions.

Namespace Permissions
---------------------

.. list-table::
    :header-rows: 1
    :widths: 20 10 10 10 10 10

    * - Role
      - Create
      - Read
      - Update
      - Delete
      - Manage Users
    * - GUEST
      - ``+``
      - ``+``
      - ``-``
      - ``-``
      - ``-``
    * - DEVELOPER
      - ``+``
      - ``+``
      - ``-``
      - ``-``
      - ``-``
    * - MAINTAINER
      - ``+``
      - ``+``
      - ``-``
      - ``-``
      - ``-``
    * - OWNER
      - ``+``
      - ``+``
      - ``+``
      - ``+``
      - ``+``
    * - SUPERADMIN
      - ``+``
      - ``+``
      - ``+``
      - ``+``
      - ``+``


HWM Permissions
---------------

.. list-table::
    :header-rows: 1
    :widths: 20 10 10 10 10

    * - Role
      - Create
      - Read
      - Update
      - Delete
    * - GUEST
      - ``-``
      - ``+``
      - ``-``
      - ``-``
    * - DEVELOPER
      - ``+``
      - ``+``
      - ``+``
      - ``-``
    * - MAINTAINER
      - ``+``
      - ``+``
      - ``+``
      - ``+``
    * - OWNER
      - ``+``
      - ``+``
      - ``+``
      - ``+``
    * - SUPERADMIN
      - ``+``
      - ``+``
      - ``+``
      - ``+``

Superadmin Role
---------------

The ``SUPERADMIN`` role grants a user unrestricted access across all entities and operations within the syncmaster service.
Users with the ``SUPERADMIN`` role can create, read, update, delete, and manage users across all ``namespaces`` and ``HWMs`` without any restrictions.

For details on how to update ``SUPERADMIN`` roles via the command-line script, see the :ref:`manage-admins-script`.

