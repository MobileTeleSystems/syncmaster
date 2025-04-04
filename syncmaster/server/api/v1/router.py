# SPDX-FileCopyrightText: 2023-2024 MTS PJSC
# SPDX-License-Identifier: Apache-2.0
from fastapi import APIRouter

from syncmaster.server.api.v1.auth import router as auth_router
from syncmaster.server.api.v1.connections import router as connection_router
from syncmaster.server.api.v1.groups import router as group_router
from syncmaster.server.api.v1.queue import router as queue_router
from syncmaster.server.api.v1.runs import router as runs_router
from syncmaster.server.api.v1.transfers import router as transfer_router
from syncmaster.server.api.v1.users import router as user_router

router = APIRouter(prefix="/v1")
router.include_router(user_router)
router.include_router(auth_router)
router.include_router(group_router)
router.include_router(connection_router)
router.include_router(transfer_router)
router.include_router(queue_router)
router.include_router(runs_router)
