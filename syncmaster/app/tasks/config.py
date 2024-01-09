# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from celery import Celery

from app.config import Settings
from app.tasks.base import WorkerTask

settings = Settings()

celery = Celery(
    __name__,
    broker=settings.build_rabbit_connection_uri(),
    backend="db+" + settings.build_db_connection_uri(driver="psycopg2"),
    task_cls=WorkerTask,
    imports=[
        "app.tasks.transfer",
    ],
)
