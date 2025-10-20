# Altering Spark session settings { #worker-create-spark-session }

SyncMaster Worker creates [SparkSession](https://spark.apache.org/docs/latest/sql-getting-started.html#starting-point-sparksession) for each Run.
By default, SparkSession is created with `master=local`, all required .jar packages for specific DB/FileSystem types, and limiter by transfer resources.

It is possible to alter SparkSession config by providing custom function:

```bash
SYNCMASTER__WORKER__CREATE_SPARK_SESSION_FUNCTION=my_worker.spark.create_custom_spark_session
```

Here is a function example:

```python
:caption: my_workers/spark.py

from syncmaster.db.models import Run
from syncmaster.dto.connections import ConnectionDTO
from pyspark.sql import SparkSession

def create_custom_spark_session(
    run: Run,
    source: ConnectionDTO,
    target: ConnectionDTO,
) -> SparkSession:
    # any custom code returning SparkSession object
    return SparkSession.builde.config(...).getOrCreate()
```

Module with custom function should be placed in the same Docker image or Python virtual environment used by SyncMaster worker.

> **For now, SyncMaster haven't been tested with `master=k8s` and `master=yarn`, so there can be some caveats.**
