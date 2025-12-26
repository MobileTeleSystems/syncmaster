# SPDX-FileCopyrightText: 2023-present MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from celery import Celery

from syncmaster.worker.base import WorkerTask
from syncmaster.worker.settings import WorkerAppSettings


def celery_factory(settings: WorkerAppSettings) -> Celery:
    return Celery(
        __name__,
        broker=settings.broker.url,
        backend="db+" + settings.database.sync_url,
        task_cls=WorkerTask,
        imports=[
            "syncmaster.worker.transfer",
        ],
    )
