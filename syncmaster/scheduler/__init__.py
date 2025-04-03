# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from celery import Celery

from syncmaster.scheduler.settings import SchedulerAppSettings


def celery_factory(settings: SchedulerAppSettings) -> Celery:
    app = Celery(
        __name__,
        broker=settings.broker.url,
        backend="db+" + settings.database.sync_url,  # noqa: WPS336
    )
    return app
