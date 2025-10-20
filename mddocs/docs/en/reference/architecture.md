# Architecture { #reference-architecture }

## Components

SyncMaster contains the following components:

- [Frontend][frontend], main user interface.
- [REST API Server][server], providing REST API for fetching and manipulating entities.
- [Worker][worker], performing actual transfer work (ETL processes).
- [Scheduler][scheduler], scheduling transfers to be executed in future.
- [Relation Database][database] for storing internal data.
- [Message Broker][message-broker] for communications between Server/Scheduler and Worker.

## Architecture diagram

![image](_static/architecture.png)
