#!/usr/bin/env bash
set -e

# https://docs.celeryq.dev/en/stable/userguide/workers.html#max-tasks-per-child-setting
# Required to start each Celery task in separated process, avoiding issues with global Spark session object

# exec is required to forward all signals to the main process
exec python -m celery -A syncmaster.worker.config.celery worker --max-tasks-per-child=1 "$@"

