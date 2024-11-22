# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from celery import Celery

from syncmaster.worker.base import WorkerTask
from syncmaster.worker.settings import WorkerAppSettings


def create_celery_app(settings) -> Celery:
    app = Celery(
        __name__,
        broker=settings.broker.url,
        backend="db+" + settings.database.sync_url,
        task_cls=WorkerTask,
        imports=[
            "syncmaster.worker.transfer",
        ],
    )
    return app


# TODO: initialize celery app in __name__ == "__main__"
#       then initialize celery app in backend via dependency injection and initialize in scheduler
celery = create_celery_app(WorkerAppSettings())
