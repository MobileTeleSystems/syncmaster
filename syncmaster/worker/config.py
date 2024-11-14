# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from celery import Celery

from syncmaster.worker.base import WorkerTask

# TODO: remove global import of WorkerSettings
from syncmaster.worker.settings import WorkerSettings as Settings

worker_settings = Settings()
celery = Celery(
    __name__,
    broker=worker_settings.broker.url,
    backend="db+" + worker_settings.database.sync_url,
    task_cls=WorkerTask,
    imports=[
        "syncmaster.worker.transfer",
    ],
)
