# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from celery import Task
from sqlalchemy import create_engine

from syncmaster.config import Settings


class WorkerTask(Task):
    def __init__(self) -> None:
        self.settings = Settings()
        self.engine = create_engine(
            url=self.settings.build_db_connection_uri(driver="psycopg2"),
        )
