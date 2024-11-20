# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from celery import Task
from sqlalchemy import create_engine

from syncmaster.worker.settings import get_worker_settings


class WorkerTask(Task):
    def __init__(self) -> None:
        self.settings = get_worker_settings()
        self.engine = create_engine(
            url=self.settings.database.sync_url,
        )
