.. title

==========
SyncMaster
==========

|Repo Status| |PyPI| |PyPI License| |PyPI Python Version| |Docker image| |Documentation|
|Build Status| |Coverage|  |pre-commit.ci|

.. |Repo Status| image:: https://www.repostatus.org/badges/latest/active.svg
    :target: https://github.com/MobileTeleSystems/syncmaster
.. |PyPI| image:: https://img.shields.io/pypi/v/data-syncmaster
    :target: https://pypi.org/project/data-syncmaster/
.. |PyPI License| image:: https://img.shields.io/pypi/l/data-syncmaster.svg
    :target: https://github.com/MobileTeleSystems/syncmaster/blob/develop/LICENSE.txt
.. |PyPI Python Version| image:: https://img.shields.io/pypi/pyversions/data-syncmaster.svg
    :target: https://badge.fury.io/py/data-syncmaster
.. |Docker image| image:: https://img.shields.io/docker/v/mtsrus/syncmaster-backend?sort=semver&label=docker
    :target: https://hub.docker.com/r/mtsrus/syncmaster-backend
.. |Documentation| image:: https://readthedocs.org/projects/syncmaster/badge/?version=stable
    :target: https://syncmaster.readthedocs.io
.. |Build Status| image:: https://github.com/MobileTeleSystems/syncmaster/workflows/Run%20All%20Tests/badge.svg
    :target: https://github.com/MobileTeleSystems/syncmaster/actions
.. |Coverage| image:: https://codecov.io/gh/MobileTeleSystems/syncmaster/graph/badge.svg?token=ky7UyUxolB
    :target: https://codecov.io/gh/MobileTeleSystems/syncmaster
.. |pre-commit.ci| image:: https://results.pre-commit.ci/badge/github/MobileTeleSystems/syncmaster/develop.svg
    :target: https://results.pre-commit.ci/latest/github/MobileTeleSystems/syncmaster/develop


What is Syncmaster?
-------------------

Syncmaster is as low-code ETL tool for transfering data between databases and file systems.
List of currently supported connections:

* Apache Hive
* Postgres
* Oracle
* HDFS
* S3

Current SyncMaster implementation provides following components:

* REST API
* Celery Worker

Goals
-----

* Make transfering data between databases and file systems as simple as possible
* Provide a lot of builtin connectors to transfer data in heterogeneous environment
* RBAC and multitenancy support

Non-goals
---------

* This is not a backup system
* This is not a CDC solution
* Only batch, no streaming

.. documentation

Documentation
-------------

See https://syncmaster.readthedocs.io