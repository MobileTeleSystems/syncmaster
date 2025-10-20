# Roles and permissions { #role-permissions }

Object within the group can be seen/interacted with only by users which are members of the group.
Permissions are limited by role assigned to user within specific group.

Roles are:

- `GUEST`
  Read-only access to objects within a group.
- `DEVELOPER`
  Read-write (manage) connections, transfers and runs. Read-only for queues.
- `MAINTAINER` (DevOps):
  Manage connections, transfers, runs and queues.
- `OWNER` (Product Owner)
  Manage connections, transfers, runs, queues and user-group membership. Group can have only one owner.
- `SUPERUSER` (Admin)
  Meta role assigned to specific users, NOT within group. All permissions, including ability to create/delete groups.
  Superusers are created by {ref}`manage-superusers-cli`.

## Groups

### Rights to work with the groups repository

| Rule Role   | Guest   | Developer   | Maintainer   | Owner   | Superuser   |
|-------------|---------|-------------|--------------|---------|-------------|
| READ        | x       | x           | x            | x       | x           |
| UPDATE      |         |             |              | x       | x           |
| CREATE      | x       | x           | x            | x       | x           |
| DELETE      |         |             |              |         | x           |

## Add user to the group and delete

Each user has the right to remove himself from a group, regardless of his role in the group.

### Rights to add/delete users to a group

| Rule Role   | Guest   | Developer   | Maintainer   | Owner   | Superuser   |
|-------------|---------|-------------|--------------|---------|-------------|
| READ        | x       | x           | x            | x       | x           |
| ADD, UPDATE |         |             |              | x       | x           |

## Transfers, and Connections

### Right to work with Transfers and Connections within a group

| Rule Role      | Guest   | Developer   | Maintainer   | Owner   | Superuser   |
|----------------|---------|-------------|--------------|---------|-------------|
| READ           | x       | x           | x            | x       | x           |
| UPDATE, CREATE |         | x           | x            | x       | x           |
| DELETE         |         |             | x            | x       | x           |

## Runs

### Right to work with Runs within a group

| Rule Role            | Guest   | Developer   | Maintainer   | Owner   | Superuser   |
|----------------------|---------|-------------|--------------|---------|-------------|
| READ                 | x       | x           | x            | x       | x           |
| CREATE (START), STOP |         | x           | x            | x       | x           |

## Queues

### Rights to work with Queues within a namespace

| Rule Role              | Guest   | Developer   | Maintainer   | Owner   | Superuser   |
|------------------------|---------|-------------|--------------|---------|-------------|
| READ                   | x       | x           | x            | x       | x           |
| UPDATE, DELETE, CREATE |         |             | x            | x       | x           |
