.. _readme:

Data.SyncMaster
===============

|Repo Status| |Docker image| |PyPI| |PyPI License| |PyPI Python Version| |Documentation|
|Build Status| |Coverage| |pre-commit.ci|

.. |Repo Status| image:: https://www.repostatus.org/badges/latest/wip.svg
    :target: https://www.repostatus.org/#wip
.. |Docker image| image:: https://img.shields.io/docker/v/mtsrus/syncmaster-server?sort=semver&label=docker
    :target: https://hub.docker.com/r/mtsrus/syncmaster-server
.. |PyPI| image:: https://img.shields.io/pypi/v/data-syncmaster
    :target: https://pypi.org/project/data-syncmaster/
.. |PyPI License| image:: https://img.shields.io/pypi/l/data-syncmaster.svg
    :target: https://github.com/MobileTeleSystems/syncmaster/blob/develop/LICENSE.txt
.. |PyPI Python Version| image:: https://img.shields.io/pypi/pyversions/data-syncmaster.svg
    :target: https://badge.fury.io/py/data-syncmaster
.. |Documentation| image:: https://readthedocs.org/projects/syncmaster/badge/?version=stable
    :target: https://syncmaster.readthedocs.io
.. |Build Status| image:: https://github.com/MobileTeleSystems/syncmaster/workflows/Run%20All%20Tests/badge.svg
    :target: https://github.com/MobileTeleSystems/syncmaster/actions
.. |Coverage| image:: https://codecov.io/gh/MobileTeleSystems/syncmaster/graph/badge.svg?token=ky7UyUxolB
    :target: https://codecov.io/gh/MobileTeleSystems/syncmaster
.. |pre-commit.ci| image:: https://results.pre-commit.ci/badge/github/MobileTeleSystems/syncmaster/develop.svg
    :target: https://results.pre-commit.ci/latest/github/MobileTeleSystems/syncmaster/develop


What is Data.SyncMaster?
------------------------

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

Based on `onETL <https://onetl.readthedocs.io/>`_ and `Apache Spark <https://spark.apache.org/>`_.

**Note**: service is under active development, and is not ready to use.

Goals
-----

* Make transfering data between databases and file systems as simple as possible
* Provide a lot of builtin connectors to transfer data in heterogeneous environment
* RBAC and multitenancy support

Non-goals
---------

* This is not a backup system
* Only batch, no streaming

.. documentation

Documentation
-------------

See https://syncmaster.readthedocs.io
