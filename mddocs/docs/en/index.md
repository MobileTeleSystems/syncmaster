# Data.SyncMaster

[![Repo Status](https://www.repostatus.org/badges/latest/wip.svg)](https://www.repostatus.org/#wip) [![Docker image](https://img.shields.io/docker/v/mtsrus/syncmaster-server?sort=semver&label=docker)](https://hub.docker.com/r/mtsrus/syncmaster-server) [![PyPI](https://img.shields.io/pypi/v/data-syncmaster)](https://pypi.org/project/data-syncmaster/) [![PyPI License](https://img.shields.io/pypi/l/data-syncmaster.svg)](https://github.com/MobileTeleSystems/syncmaster/blob/develop/LICENSE.txt) [![PyPI Python Version](https://img.shields.io/pypi/pyversions/data-syncmaster.svg)](https://badge.fury.io/py/data-syncmaster) [![Documentation](https://readthedocs.org/projects/syncmaster/badge/?version=stable)](https://syncmaster.readthedocs.io)
[![Build Status](https://github.com/MobileTeleSystems/syncmaster/workflows/Run%20All%20Tests/badge.svg)](https://github.com/MobileTeleSystems/syncmaster/actions) [![Coverage](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/MTSOnGithub/03e73a82ecc4709934540ce8201cc3b4/raw/syncmaster_badge.json)](https://github.com/MobileTeleSystems/syncmaster/actions) [![pre-commit.ci](https://results.pre-commit.ci/badge/github/MobileTeleSystems/syncmaster/develop.svg)](https://results.pre-commit.ci/latest/github/MobileTeleSystems/syncmaster/develop)

## What is Data.SyncMaster?

Data.SyncMaster is as low-code ETL tool for transfering data between databases and file systems.
List of currently supported connections:

* Apache Hive
* Clickhouse
* Postgres
* Oracle
* MSSQL
* MySQL
* HDFS
* S3
* FTP
* FTPS
* SFTP
* Samba
* WebDAV

Based on [onETL](https://onetl.readthedocs.io/) and [Apache Spark](https://spark.apache.org/).

**Note**: service is under active development, and is not ready to use.

## Goals

* Make transfering data between databases and file systems as simple as possible
* Provide a lot of builtin connectors to transfer data in heterogeneous environment
* RBAC and multitenancy support

## Non-goals

* This is not a backup system
* Only batch, no streaming

High-level design

* [Entities][entities]
* [Permissions][role-permissions]

Reference

* [Architecture][reference-architecture]
* [Database][database]
* [Broker][message-broker]
* [Server][server]
* [Frontend][frontend]
* [Worker][worker]
* [Scheduler][scheduler]

Development

* [Changelog][changelog]
* [Contributing][contributing]
* [Security][security]
