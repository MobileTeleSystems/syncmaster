.. _worker-create-spark-session:

Configuring Spark session
=========================

SyncMaster Worker creates `SparkSession <https://spark.apache.org/docs/latest/sql-getting-started.html#starting-point-sparksession>`_ for each Run.

By default, SparkSession is created with ``spark.master: local``, including all required .jar packages for DB/FileSystem types, and limited by transfer resources.

Custom Spark session configuration
----------------------------------

It is possible to alter default `Spark Session configuration <https://spark.apache.org/docs/latest/configuration.html>`_ worker settings:

.. code-block:: yaml
    :caption: config.yml

    worker:
        spark_session_default_config:
            spark.master: local
            spark.driver.host: 127.0.0.1
            spark.driver.bindAddress: 0.0.0.0
            spark.sql.pyspark.jvmStacktrace.enabled: true
            spark.ui.enabled: false

For example, to use SyncMaster on Spark-on-K8s, you can use worker image for Spark executor containers:

.. code-block:: yaml
    :caption: config.yml

    worker:
        spark_session_default_config:
            spark.master: k8s://https://kubernetes.default.svc
            spark.driver.host: service-for-spark-driver
            spark.driver.bindAddress: 0.0.0.0
            spark.driver.port: 10000
            spark.blockManager.port: 10001
            spark.kubernetes.authenticate.driver.serviceAccountName: spark
            spark.sql.pyspark.jvmStacktrace.enabled: true
            spark.kubernetes.container.image: mtsrus/syncmaster-worker:{TAG}

.. note::

    Currently Spark-on-K8s and Spark-on-Yarn do not support interaction FTP, FTPS, SFTP, Samba and WebDAV.
    This requires  ``sparm.master: local``.

Custom Spark session factory
----------------------------

It is also possible to use custom function which returns ``SparkSession`` object:

.. code-block:: yaml
    :caption: config.yml

    worker:
        create_spark_session_function: my_worker.spark.create_custom_spark_session

Here is a function example:

.. code-block:: python
    :caption: my_workers/spark.py

    from syncmaster.db.models import Run
    from syncmaster.dto.connections import ConnectionDTO
    from syncmaster.worker.settings import WorkerSettings
    from pyspark.sql import SparkSession

    def create_custom_spark_session(
        run: Run,
        source: ConnectionDTO,
        target: ConnectionDTO,
        settings: WorkerSettings,
    ) -> SparkSession:
        # any custom code returning SparkSession object
        return SparkSession.builde.config(...).getOrCreate()

Module with custom function should be placed into the same Docker image or Python virtual environment used by SyncMaster worker.
