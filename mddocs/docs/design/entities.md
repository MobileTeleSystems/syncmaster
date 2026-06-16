# Entities { #entities }

## User

SyncMaster is designed with multitenancy support and role-based access (see [Roles and permissions][role-permissions]).
All nteraction requires user authentication, there is no anonymous access allowed.

Users are automatically after successful login, there is no special registration step.

## Group

All entity types (Connection, Transfer, Run, Queue) can be created only within some group.
Groups are independent from each other, and have globally unique name.

![image](entities/group_list.png)

![image](entities/group_info.png)

Group can be created by any user, which automatically get `OWNER` role.
This role allows adding members to the group, and assign them specific roles:

![image](entities/group_add_member.png)

## Connection

Connection describes how SyncMaster can access specific database or filesystem. It has a type (e.g. `s3`, `hive`, `postgres`),
connection parameters (e.g. `host`, `port`, `protocol`) and auth data (`user` / `password` combination).

Connections have unique name within the group.

![image](entities/connection_list.png)![image](entities/connection_info_db.png)![image](entities/connection_info_fs.png)

## Transfer

Transfer is the heart of SyncMaster. It describes what some data should be fetched from a source (DB connection + table name, FileSystem connection + directory path),
and what the target is (DB or FileSystem).

Transfers have unique name within a group.

![image](entities/transfer_list.png)![image](entities/create_transfer_head.png)![image](entities/create_transfer_source_target.png)![image](entities/create_transfer_advanced.png)

It is possible to add transformations between reading and writing steps:

![image](entities/create_transfer_advanced_filter_files.png)![image](entities/create_transfer_advanced_filter_rows.png)![image](entities/create_transfer_advanced_filter_columns.png)

Other transfer features are:

- Choose different read strategies (`full`, `incremental`)
- Execute transfer on schedule (hourly, daily, weekly and so on)
- Set specific resources (CPU, RAM) for each transfer run

![image](entities/create_transfer_footer.png)

## Run

Each time transfer is started (manually or at some schedule), SyncMaster creates dedicated Run
which tracks the ETL process status, URL to worker logs and so on.

![image](entities/run_list.png)![image](entities/run_info.png)

## Queue

Queue allows to bind specific transfer to a set of SyncMaster [Worker][worker]

Queue have unique name within a group, and globally unique `slug` field which is generated during queue creation.

![image](entities/queue_list.png)![image](entities/queue_info.png)

Transfers cannot be created without queue. If there are no workers bound to a queue, created runs will not be executed.

## Entity Diagram

```mermaid
---
title: Entity Diagram
---
erDiagram
    direction LR
    User {
        number id
        string username
        string is_active
        string is_superuser
        string created_at
        string updated_at
    }

    Group {
        number id
        string name
        string description
        number owner_id
        string created_at
        string updated_at
    }

    Connection {
        number id
        number group_id
        string type
        string name
        string description
        string data
        string created_at
        string updated_at
    }

    Queue {
        number id
        string name
        string slug
        string description
        string created_at
        string updated_at
    }


    Transfer {
        number id
        number group_id
        string name
        number source_connection_id
        number target_connection_id
        string strategy_params
        string target_params
        string transformations
        string resources
        string is_scheduled
        string schedule
        number queue_id
        string created_at
        string updated_at
    }

    Run {
        number id
        number transfer_id
        string started_at
        string ended_at
        string status
        string type
        string log_url
        string transfer_dump
        string created_at
        string updated_at
    }

    Run ||--o{ Transfer: contains

    Transfer ||--o{ Queue: contains
    Transfer ||--o{ Connection: contains
    Transfer ||--o{ Group: contains
    Connection ||--o{ Group: contains
    Queue ||--o{ Group: contains
    Group }o--o{ User: contains
    Group ||--o{ User: contains
```
