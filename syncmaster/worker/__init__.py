# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from celery import Celery

from syncmaster.worker.base import WorkerTask
from syncmaster.worker.settings import WorkerAppSettings


def celery_factory(settings: WorkerAppSettings) -> Celery:
    app = Celery(
        __name__,
        broker=settings.broker.url,
        backend="db+" + settings.database.sync_url,  # noqa: WPS336
        task_cls=WorkerTask,
        imports=[
            "syncmaster.worker.transfer",
        ],
    )
    return app
