# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.scheduler.settings import SchedulerAppSettings
from syncmaster.worker import celery_factory

app = celery_factory(SchedulerAppSettings())
