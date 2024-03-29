.. _role-permissions:

Roles and permissions
=====================

- Object within the group can be seen/interacted with only by users which are members of the group.
- Permissions are limited by role assigned to user within specific group.
- There can be only one user in a group with the Owner role, all other roles are not limited in
  number.
- Superuser can read, write to the table and delete without being in the group.

Roles are:

* ``GUEST`` - read-only
* ``DEVELOPER`` - read-write
* ``MAINTAINER`` (DevOps) - read-write + manage queues
* ``OWNER`` (Product Owner) - read-write + manage queues + manage user-group mapping
* ``SUPERUSER`` - meta role assigned to specific users (NOT within group). Read-write + manage queues + manage user-group mapping + create/delete groups.


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
