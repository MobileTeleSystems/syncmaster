# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from fastapi import APIRouter

from syncmaster.server.api import monitoring
from syncmaster.server.api.v1.router import router as v1_router

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(v1_router)
