# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from backend.config import Settings
from backend.worker.base import WorkerTask
from celery import Celery

settings = Settings()

celery = Celery(
    __name__,
    broker=settings.build_rabbit_connection_uri(),
    backend="db+" + settings.build_db_connection_uri(driver="psycopg2"),
    task_cls=WorkerTask,
    imports=[
        "backend.worker.transfer",
    ],
)
