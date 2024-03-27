.. _entities:

Entities
========

HWM
---

Description
~~~~~~~~~~~

High Water Mark (or *HWM* for short) is a record which allows tracking state of operations (usually read). For example:
    * Save max value of a column read from a table (e.g. ``updated_at``), and then use it exclude already read rows on the next read.
    * Save list of files handled by a process, and then use it to exclude these files on the next read.
    * Same max modification time of files handled by a process, and then use it to exclude these files on the next read.

Each HWM record is bound to a specific Namespace. HWM ``name`` is unique within this Namespace.

Users may create unlimited number of HWMs within a namespace.

Fields
~~~~~~

HWM record has following fields:
    * ``id: integer`` - internal HWM identifier, generated using sequence, read only.
    * ``namespace_id: integer`` - bound to a Namespace, mandatory.
    * ``name: string`` - unique name within a Namespace, mandatory.
    * ``value: json`` - value associated with HWM, mandatory.
    * ``type: string`` - any string describing type of ``value`` field content, mandatory.
    * ``description: string`` - human readable description.
    * ``entity: string | null`` - name of entity (e.g. table name, folder) which value is bound to.
    * ``expression: string | null`` - expression (e.g. column name) used to get value from ``entity``.
    * ``changed_at: datetime`` - filled up automatically on each item change, read only.
    * ``changed_by: User | null`` - filled up automatically on each item change, read only.

``type`` and ``value`` can contain any value, and are not parsed or checked by backend. This allows users to create HWMs of any type in any time,
without patching backend. But it is up to user to keep consistency of these fields.

Limitations
~~~~~~~~~~~

HWM cannot be moved between namespaces. Users have to explicitly create a copy of existing HWM in new namespace,
and delete old HWM.

Namespace
---------

Description
~~~~~~~~~~~

Namespace is a container for HWM records.

Each namespace has an owner which can alter namespace properties, see :ref:`role-permissions`.

Users may create unlimited number of namespaces. If user created a namespace, it is automatically set as the namespace owner.

Fields
~~~~~~~~~~~

Namespace record has following fields:
    * ``id: integer`` - internal namespace identifier, generated using sequence, read only.
    * ``name: string`` - unique per syncmaster instance, mandatory
    * ``description: string`` - human readable description.
    * ``owned_by: User`` - is set automatically while namespace is created, mandatory.
    * ``changed_at: datetime`` - filled up automatically on each item change, read only.
    * ``changed_by: User | null`` - filled up automatically on each item change, read only.

User
----

Description
~~~~~~~~~~~

Users are used for:
    * Authentication
    * RBAC permissions model
    * Keeping track of changes made on Namespace or HWM.

User records are created automatically after successful authentication.

Fields
~~~~~~

User record has following fields:
    * ``id: integer`` - internal user identifier, generated using sequence, read only
    * ``username: string`` - unique per syncmaster instance
    * ``is_active: boolean`` - flag if user is allowed to log in.
    * ``is_admin: boolean`` - flag for SUPERUSER role.

Limitations
~~~~~~~~~~~

For now it is not possible to remove user after creation.

Permission
----------

Description
~~~~~~~~~~~

User can be assigned a Role within a Namespace, which can allow or disallow performing specific operation within this Namespace.
User can have different roles in different namespaces. See :ref:`role-permissions`.

Fields
~~~~~~

Permission record has following fields:
  * ``user: User``
  * ``namespace: Namespace``
  * ``role: enum``.

Limitations
~~~~~~~~~~~

User can be assigned only one Role within a Namespace.

NamespaceHistory
----------------

Description
~~~~~~~~~~~

Change of each Namespace value produces a HWMHistory item, which can be used for audit purpose.
History is append-only, items cannot be changed or deleted using API.

Fields
~~~~~~

NamespaceHistory record has following fields (all read-only):
    * ``id: integer`` - internal history item identifier, generated using sequence.
    * ``namespace_id: integer`` - bound to Namespace item.
    * ``name: string``.
    * ``description: string``.
    * ``owned_by: User``.
    * ``changed_at: datetime`` - filled up automatically on each item change.
    * ``changed_by: User | null`` - filled up automatically on each item change.
    * ``action: string`` - change description, e.g. ``Created``, ``Updated``, ``Deleted``.

HWMHistory
----------

Description
~~~~~~~~~~~

Change of each HWM value produces a HWMHistory item, which can be used for audit purpose.
History is append-only, items cannot be changed or deleted using API.

Fields
~~~~~~

HWMHistory record has following fields (all read-only):
    * ``id: integer`` - internal history item identifier, generated using sequence.
    * ``hwm_id: integer`` - bound to HWM item.
    * ``name: string``.
    * ``value: any | null``.
    * ``type: string``.
    * ``description: string``.
    * ``entity: string | null``.
    * ``expression: string | null``.
    * ``changed_at: datetime`` - filled up automatically on each item change.
    * ``changed_by: User | null`` - filled up automatically on each item change.
    * ``action: string`` - change description, e.g. ``Created``, ``Updated``, ``Deleted``.

Entity Diagram
--------------

.. plantuml::

    @startuml
    title Entity Diagram

    left to right direction

    entity User {
        * id
        ----
        * username
        is_active
        is_admin
    }

    entity Namespace {
        * id
        ----
        * namespace_id
        * name
        * owned_by
        description
        changed_at
        changed_by
    }

    entity HWM {
        * id
        ----
        * name
        * type
        * value
        description
        entity
        expression
        changed_at
        changed_by
    }

    entity NamespaceHistory {
        * id
        ----
        * namespace_id
        name
        owned_by
        description
        changed_at
        changed_by
        action
    }

    entity HWMHistory {
        * id
        ----
        * hwm_id
        * namespace_id
        name
        type
        value
        description
        entity
        expression
        changed_at
        changed_by
        action
    }

    entity Permission {
        * user_id
        * namespace_id
        ----
        * role
    }

    HWM ||--o{ Namespace
    Namespace }o--o| NamespaceHistory
    HWM }o--o| HWMHistory
    Namespace "owner" ||--o{ User
    Namespace }o--|| Permission
    Permission ||--o{ User

    @enduml
