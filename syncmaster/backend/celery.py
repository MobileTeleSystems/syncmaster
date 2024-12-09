# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from syncmaster.backend.settings import ServerAppSettings
from syncmaster.worker import celery_factory

app = celery_factory(ServerAppSettings())
