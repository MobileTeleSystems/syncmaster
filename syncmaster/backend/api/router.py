# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from backend.api import monitoring
from backend.api.v1.router import router as v1_router
from fastapi import APIRouter

api_router = APIRouter()
api_router.include_router(monitoring.router)
api_router.include_router(v1_router)
