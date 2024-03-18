# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from celery import Celery

from syncmaster.config import Settings
from syncmaster.worker.base import WorkerTask

settings = Settings()

celery = Celery(
    __name__,
    broker=settings.build_rabbit_connection_uri(),
    backend="db+" + settings.build_db_connection_uri(driver="psycopg2"),
    task_cls=WorkerTask,
    imports=[
        "syncmaster.worker.transfer",
    ],
)
