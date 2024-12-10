# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.scheduler import celery_factory
from syncmaster.scheduler.settings import SchedulerAppSettings

# Global object, since the TransferJobManager.send_job_to_celery method is static
app = celery_factory(SchedulerAppSettings())
