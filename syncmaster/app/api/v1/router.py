# SPDX-FileCopyrightText: 2023-2024 MTS (Mobile Telesystems)
# SPDX-License-Identifier: Apache-2.0
from fastapi import APIRouter

from app.api.v1.auth.router import router as auth_router
from app.api.v1.connections.router import router as connection_router
from app.api.v1.groups.router import router as group_router
from app.api.v1.queue.router import router as queue_router
from app.api.v1.transfers.router import router as transfer_router
from app.api.v1.users.router import router as user_router

router = APIRouter(prefix="/v1")
router.include_router(user_router)
router.include_router(auth_router)
router.include_router(group_router)
router.include_router(connection_router)
router.include_router(transfer_router)
router.include_router(queue_router)
