#!/usr/bin/env bash

# Based on https://github.com/apache/spark/blob/v3.5.7/resource-managers/kubernetes/docker/src/main/dockerfiles/spark/entrypoint.sh

set -ex

if [ -z "$JAVA_HOME" ]; then
  JAVA_HOME=$(java -XshowSettings:properties -version 2>&1 > /dev/null | grep 'java.home' | awk '{print $3}')
fi
if [ -z "$SPARK_HOME" ]; then
  SPARK_HOME=$(python -c 'import pyspark; import pathlib; print(pathlib.Path(pyspark.__file__).parent.resolve())')
fi

SPARK_CLASSPATH="$SPARK_CLASSPATH:${SPARK_HOME}/jars/*"

JAVA_OPTS_FILE=$(mktemp)
env | grep SPARK_JAVA_OPT_ | sort -t_ -k4 -n | sed 's/[^=]*=\(.*\)/\1/g' > $JAVA_OPTS_FILE
if [ "$(command -v readarray)" ]; then
  readarray -t SPARK_EXECUTOR_JAVA_OPTS < $JAVA_OPTS_FILE
else
  SPARK_EXECUTOR_JAVA_OPTS=("${(@f)$(< $JAVA_OPTS_FILE)}")
fi

if [ -n "$SPARK_EXTRA_CLASSPATH" ]; then
  SPARK_CLASSPATH="$SPARK_CLASSPATH:$SPARK_EXTRA_CLASSPATH"
fi

if ! [ -z ${PYSPARK_PYTHON+x} ]; then
    export PYSPARK_PYTHON
fi
if ! [ -z ${PYSPARK_DRIVER_PYTHON+x} ]; then
    export PYSPARK_DRIVER_PYTHON
fi

# If HADOOP_HOME is set and SPARK_DIST_CLASSPATH is not set, set it here so Hadoop jars are available to the executor.
# It does not set SPARK_DIST_CLASSPATH if already set, to avoid overriding customizations of this value from elsewhere e.g. Docker/K8s.
if [ -n "${HADOOP_HOME}"  ] && [ -z "${SPARK_DIST_CLASSPATH}"  ]; then
  export SPARK_DIST_CLASSPATH="$($HADOOP_HOME/bin/hadoop classpath)"
fi

if ! [ -z ${HADOOP_CONF_DIR+x} ]; then
  SPARK_CLASSPATH="$HADOOP_CONF_DIR:$SPARK_CLASSPATH";
fi

if ! [ -z ${SPARK_CONF_DIR+x} ]; then
  SPARK_CLASSPATH="$SPARK_CONF_DIR:$SPARK_CLASSPATH";
elif ! [ -z ${SPARK_HOME+x} ]; then
  SPARK_CLASSPATH="$SPARK_HOME/conf:$SPARK_CLASSPATH";
fi

# SPARK-43540: add current working directory into executor classpath
SPARK_CLASSPATH="$SPARK_CLASSPATH:$PWD"

if ! [ -n ${SPARK_LOCAL_DIRS} ]; then
  CURRENT_DIR=$(mktemp -d)
else
  # /var/data/spark-local-123,/var/data/spark-local-234 -> /var/data/spark-local-123
  CURRENT_DIR=${SPARK_LOCAL_DIRS%%,*}
fi

# current dir should always be writable
cd "${CURRENT_DIR}"

case "$1" in
  driver)
    shift 1
    CMD=(
      "$SPARK_HOME/bin/spark-submit"
      --conf "spark.driver.bindAddress=$SPARK_DRIVER_BIND_ADDRESS"
      --conf "spark.executorEnv.SPARK_DRIVER_POD_IP=$SPARK_DRIVER_BIND_ADDRESS"
      --deploy-mode client
      "$@"
    )
    ;;
  executor)
    shift 1
    CMD=(
      ${JAVA_HOME}/bin/java
      "${SPARK_EXECUTOR_JAVA_OPTS[@]}"
      -Xms$SPARK_EXECUTOR_MEMORY
      -Xmx$SPARK_EXECUTOR_MEMORY
      -cp "$SPARK_CLASSPATH:$SPARK_DIST_CLASSPATH"
      org.apache.spark.scheduler.cluster.k8s.KubernetesExecutorBackend
      --driver-url $SPARK_DRIVER_URL
      --executor-id $SPARK_EXECUTOR_ID
      --cores $SPARK_EXECUTOR_CORES
      --app-id $SPARK_APPLICATION_ID
      --hostname $SPARK_EXECUTOR_POD_IP
      --resourceProfileId $SPARK_RESOURCE_PROFILE_ID
      --podName $SPARK_EXECUTOR_POD_NAME
    )
    ;;

  worker)
    shift 1
    # https://docs.celeryq.dev/en/stable/userguide/workers.html#max-tasks-per-child-setting
    # Required to start each Celery task in separated process, avoiding issues with global Spark session object
    CMD=(
      python -m celery
      -A syncmaster.worker.celery
      worker
      --max-tasks-per-child=1
      "$@"
    )
    ;;

  # Any other command to run
  *)
    CMD=("$@")
esac

# Execute the container CMD under tini for better hygiene
exec /usr/bin/tini -s -- "${CMD[@]}"
