.. _role-permissions:

Roles and permissions
=====================


Object within the group can be seen/interacted with only by users which are members of the group.
Permissions are limited by role assigned to user within specific group.

Roles are:

* ``GUEST``
  Read-only access to objects within a group.
* ``DEVELOPER``
  Read-write (manage) connections and transfer, read-only for other objects.
* ``MAINTAINER`` (DevOps):
  Manage connections, transfers and queues.
* ``OWNER`` (Product Owner)
  Manage connections, transfers, queues and user-group membership. Group can have only one maintainer.
* ``SUPERUSER`` (Admin)
  Meta role assigned to specific users, NOT within group. All permissions, including ability to create/delete groups.
  Superusers are created by :ref:`manage-superusers-cli`.

Groups
-------

.. list-table:: Rights to work with the groups repository.
   :header-rows: 1

   * - Rule \ Role
     - Guest
     - Developer
     - Maintainer
     - Owner
     - Superuser
   * - READ
     - x
     - x
     - x
     - x
     - x
   * - UPDATE
     -
     -
     -
     - x
     - x
   * - CREATE
     - x
     - x
     - x
     - x
     - x
   * - DELETE
     -
     -
     -
     -
     - x

Add user to the group and delete
---------------------------------
Each user has the right to remove himself from a group, regardless of his role in the group.

.. list-table:: Rights to delete and add users to a group.
   :header-rows: 1

   * - Rule \ Role
     - Guest
     - Developer
     - Maintainer
     - Owner
     - Superuser
   * - READ
     - x
     - x
     - x
     - x
     - x
   * - ADD, UPDATE
     -
     -
     -
     - x
     - x

Transfers, Runs and Connections
--------------------------------

.. list-table:: Right to work wirh Transfers, Runs and Connections repositories.
   :header-rows: 1


   * - Rule \ Role
     - Guest
     - Developer
     - Maintainer
     - Owner
     - Superuser
   * - READ
     - x
     - x
     - x
     - x
     - x
   * - UPDATE, CREATE
     -
     - x
     - x
     - x
     - x
   * - DELETE
     -
     -
     - x
     - x
     - x

Queues
------

.. list-table:: Rights to read, delete and update queues.
   :header-rows: 1

   * - Rule \ Role
     - Guest
     - Developer
     - Maintainer
     - Owner
     - Superuser
   * - READ
     - x
     - x
     - x
     - x
     - x
   * - UPDATE, DELETE, CREATE
     -
     -
     - x
     - x
     - x
