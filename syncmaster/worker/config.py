# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from celery import Celery

from syncmaster.settings import Settings
from syncmaster.worker.base import WorkerTask

settings = Settings()

celery = Celery(
    __name__,
    broker=settings.broker.url,
    backend="db+" + settings.database.sync_url,
    task_cls=WorkerTask,
    imports=[
        "syncmaster.worker.transfer",
    ],
)
