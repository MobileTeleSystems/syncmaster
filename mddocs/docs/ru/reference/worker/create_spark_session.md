# Изменение настроек Spark сессии { #worker-create-spark-session }

SyncMaster Worker(рабочий процесс) создает [SparkSession](https://spark.apache.org/docs/latest/sql-getting-started.html#starting-point-sparksession) для каждого запуска.
По умолчанию, SparkSession создается с параметрами `master=local`, всеми необходимыми .jar пакетами для конкретных типов БД/Файловых систем и ограничителем по ресурсам передачи данных.

Можно изменить конфигурацию SparkSession, предоставив пользовательскую функцию:

```bash
SYNCMASTER__WORKER__CREATE_SPARK_SESSION_FUNCTION=my_worker.spark.create_custom_spark_session
```

Вот пример функции:

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
    # любой пользовательский код, возвращающий объект SparkSession
    return SparkSession.builde.config(...).getOrCreate()
```

Модуль с пользовательской функцией должен быть размещен в том же Docker-образе или виртуальном окружении Python, которое используется SyncMaster worker.

> **На данный момент SyncMaster не тестировался с `master=k8s` и `master=yarn`, поэтому могут быть некоторые особенности.**
