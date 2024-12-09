# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.worker import celery_factory
from syncmaster.worker.settings import WorkerAppSettings

app = celery_factory(WorkerAppSettings())
